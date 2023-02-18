"""
Custom integration to integrate Saleryd HRV system with Home Assistant.
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration
from pysaleryd.client import Client

from .const import (
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from .coordinator import SalerydLokeDataUpdateCoordinator

SCAN_INTERVAL = timedelta(seconds=5)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP_MESSAGE, integration.version)

    url = entry.data.get(CONF_WEBSOCKET_IP)
    port = entry.data.get(CONF_WEBSOCKET_PORT)

    session = async_get_clientsession(hass)
    client = Client(url, port, session)
    try:
        await client.connect()
    except (asyncio.TimeoutError, TimeoutError) as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting to {url}:{port}") from ex

    coordinator = SalerydLokeDataUpdateCoordinator(
        hass,
        client,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

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
        await client.send_command(key, value)

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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator: SalerydLokeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.disconnect()

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
