"""
Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/integration_blueprint
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SalerydLokeApiClient

from .const import (
    CONF_WEBSOCKET_URL,
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

    url = entry.data.get(CONF_WEBSOCKET_URL)

    session = async_get_clientsession(hass)
    client = SalerydLokeApiClient(url, session)

    coordinator = SalerydLokeDataUpdateCoordinator(hass, client=client)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    # Register services
    async def control_request(cmd_name, value=None):
        cmd = f"#{cmd_name}:{value}"
        _LOGGER.info("Sending control request %s with payload %s", cmd_name, value)
        await client.async_send_command(data=cmd)

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

    def __init__(self, hass: HomeAssistant, client: SalerydLokeApiClient) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            return await self.api.async_get_data()
        except Exception as exception:
            raise UpdateFailed() from exception


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
