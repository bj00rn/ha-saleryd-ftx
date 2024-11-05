"""
Custom integration to integrate Saleryd HRV system with Home Assistant.
"""

import asyncio
from datetime import timedelta

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_integration
from pysaleryd.client import Client

from .const import (
    CONF_ENABLE_MAINTENANCE_SETTINGS,
    CONF_MAINTENANCE_PASSWORD,
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    CONFIG_VERSION,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    SERVICE_SET_COOLING_MODE,
    SERVICE_SET_FIREPLACE_MODE,
    SERVICE_SET_SYSTEM_ACTIVE_MODE,
    SERVICE_SET_TARGET_TEMPERATURE_COOL,
    SERVICE_SET_TARGET_TEMPERATURE_ECONOMY,
    SERVICE_SET_TARGET_TEMPERATURE_NORMAL,
    SERVICE_SET_TEMPERATURE_MODE,
    SERVICE_SET_VENTILATION_MODE,
    STARTUP_MESSAGE,
)
from .coordinator import SalerydLokeDataUpdateCoordinator

SCAN_INTERVAL = timedelta(seconds=30)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry."""

    if entry.version is not None and entry.version > CONFIG_VERSION:
        # This means the user has downgraded from a future version
        return False

    if entry.version is None or entry.version == 1:
        new_data = entry.data.copy()
        new_data |= {
            CONF_ENABLE_MAINTENANCE_SETTINGS: False,
            CONF_MAINTENANCE_PASSWORD: None,
        }

        LOGGER.info("Upgrading entry from version 1")
        hass.config_entries.async_update_entry(
            entry, data=new_data, version=CONFIG_VERSION
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    integration = await async_get_integration(hass, DOMAIN)
    LOGGER.info(STARTUP_MESSAGE, integration.version)

    url = entry.data.get(CONF_WEBSOCKET_IP)
    port = entry.data.get(CONF_WEBSOCKET_PORT)

    session = async_create_clientsession(hass, raise_for_status=True)
    client = Client(url, port, session, SCAN_INTERVAL.seconds)
    try:
        async with async_timeout.timeout(10):
            await client.connect()
    except (TimeoutError, asyncio.CancelledError) as ex:
        client.disconnect()
        raise ConfigEntryNotReady(f"Timeout while connecting to {url}:{port}") from ex
    else:
        coordinator = SalerydLokeDataUpdateCoordinator(hass, client, LOGGER)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def control_request(key, value=None, authenticate=False):
        """Helper for system control calls"""
        if authenticate:
            maintenance_password = entry.data.get(CONF_MAINTENANCE_PASSWORD)
            LOGGER.debug("Unlock maintenance settings control request")
            await client.send_command("IP", maintenance_password)

        LOGGER.debug("Sending control request %s with payload %s", key, value)
        await client.send_command(key, value)

    async def set_fireplace_mode(call):
        """Set fireplace mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set fire mode request of %s", value)
        await control_request("MB", value)

    async def set_ventilation_mode(call):
        """Set ventilation mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set ventilation mode request of %s", value)
        await control_request("MF", value)

    async def set_temperature_mode(call):
        """Set temperature mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set temperature mode request of %s", value)
        await control_request("MT", value)

    async def set_cooling_mode(call):
        """Set cooling mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set cooling mode request of %s", value)
        await control_request("MK", value)

    async def set_system_active_mode(call):
        """Set system active mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending system active mode request of %s", value)
        await control_request("MP", value, True)

    async def set_target_temperature_cool(call):
        """Set target temperature for Cool temperature mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for Cool mode of %s", value)
        await control_request("TF", value, True)

    async def set_target_temperature_normal(call):
        """Set target temperature for Normal temperature mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for Normal mode of %s", value)
        await control_request("TD", value, True)

    async def set_target_temperature_economy(call):
        """Set target temperature for Economy temperature mode"""
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for Economy mode of %s", value)
        await control_request("TE", value, True)

    services = {
        SERVICE_SET_FIREPLACE_MODE: set_fireplace_mode,
        SERVICE_SET_COOLING_MODE: set_cooling_mode,
        SERVICE_SET_VENTILATION_MODE: set_ventilation_mode,
        SERVICE_SET_TEMPERATURE_MODE: set_temperature_mode,
    }

    maintenance_services = {
        SERVICE_SET_SYSTEM_ACTIVE_MODE: set_system_active_mode,
        SERVICE_SET_TARGET_TEMPERATURE_COOL: set_target_temperature_cool,
        SERVICE_SET_TARGET_TEMPERATURE_ECONOMY: set_target_temperature_economy,
        SERVICE_SET_TARGET_TEMPERATURE_NORMAL: set_target_temperature_normal,
    }

    # register services
    for key, fn in services.items():
        hass.services.async_register(DOMAIN, key, fn)

    # register maintenance services
    if entry.data.get(CONF_ENABLE_MAINTENANCE_SETTINGS):
        for key, fn in maintenance_services.items():
            hass.services.async_register(DOMAIN, key, fn)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""

    # disconnect client
    coordinator: SalerydLokeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.disconnect()

    # remove services
    for key in hass.services.async_services().get(DOMAIN, dict()):
        hass.services.async_remove(DOMAIN, key)

    # unload platforms
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
