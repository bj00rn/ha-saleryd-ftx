"""
Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/integration_blueprint
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady
from .gateway import Gateway

from .const import (
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    url = entry.data.get(CONF_WEBSOCKET_IP)
    port = entry.data.get(CONF_WEBSOCKET_PORT)

    session = async_get_clientsession(hass)
    gateway = Gateway(session, url, port)
    coordinator = SalerydLokeDataUpdateCoordinator(hass, gateway)

    async def callback():

        while True:
            if coordinator.data:
                return True
            if not coordinator.last_update_success:
                raise ConfigEntryNotReady
            await asyncio.sleep(1)

    await asyncio.gather(callback())

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    # Register services
    async def control_request(key, value=None):
        _LOGGER.info("Sending control request %s with payload %s", key, value)
        await gateway.send_command(key, value)

    async def set_fireplace_mode(call):
        value = call.data.get("value")
        _LOGGER.info("Sending set fire mode request of %s", value)
        await control_request("MB", value)

    async def set_ventilation_mode(call):
        value = call.data.get("value")
        _LOGGER.info("Sending set ventilation mode request of %s", value)
        await control_request("MF", value)

    async def set_temperature_mode(call):
        value = call.data.get("value")
        _LOGGER.info("Sending set temperature mode request of %s", value)
        await control_request("MT", value)

    async def set_cooling_mode(call):
        value = call.data.get("value")
        _LOGGER.info("Sending set cooling mode request of %s", value)
        await control_request("MK", value)

    hass.services.async_register(DOMAIN, "set_fireplace_mode", set_fireplace_mode)
    hass.services.async_register(DOMAIN, "set_cooling_mode", set_cooling_mode)
    hass.services.async_register(DOMAIN, "set_ventilation_mode", set_ventilation_mode)
    hass.services.async_register(DOMAIN, "set_temperature_mode", set_temperature_mode)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, gateway: Gateway) -> None:
        """Initialize."""
        self._gateway = gateway

        self.platforms = []

        self._gateway.add_handler(self.async_set_updated_data)

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @Throttle(timedelta(seconds=10))
    def async_set_updated_data(self, data) -> None:
        super().async_set_updated_data(data)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
