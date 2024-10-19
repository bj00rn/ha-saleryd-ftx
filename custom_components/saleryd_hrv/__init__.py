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
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
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
    SERVICE_UNLOCK_MAINTENANCE_SETTINGS,
    STARTUP_MESSAGE,
)
from .coordinator import SalerydLokeDataUpdateCoordinator

SCAN_INTERVAL = timedelta(seconds=30)


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
        for platform in PLATFORMS:
            if entry.options.get(platform, True):
                coordinator.platforms.append(platform)
                hass.async_add_job(
                    hass.config_entries.async_forward_entry_setup(entry, platform)
                )

    # Register services
    async def control_request(key, value=None):
        LOGGER.debug("Sending control request %s with payload %s", key, value)
        await client.send_command(key, value)

    async def set_fireplace_mode(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set fire mode request of %s", value)
        await control_request("MB", value)

    async def set_ventilation_mode(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set ventilation mode request of %s", value)
        await control_request("MF", value)

    async def set_temperature_mode(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set temperature mode request of %s", value)
        await control_request("MT", value)

    async def set_cooling_mode(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set cooling mode request of %s", value)
        await control_request("MK", value)

    async def unlock_maintenance_settings(call):
        value = call.data.get("value")
        LOGGER.debug(
            "Sending unlock maintenance settings request with passsword <redacted>"
        )
        await control_request("IP", value)

    async def set_system_active_mode(call):
        value = call.data.get("value")
        LOGGER.debug("Sending system active mode request of %s", value)
        await control_request("MP", value)

    async def set_target_temperature_cool(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for cool mode of %s", value)
        await control_request("TF", value)

    async def set_target_temperature_normal(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for normal mode of %s", value)
        await control_request("TD", value)

    async def set_target_temperature_economy(call):
        value = call.data.get("value")
        LOGGER.debug("Sending set target temperature for economy mode of %s", value)
        await control_request("TE", value)

    hass.services.async_register(DOMAIN, SERVICE_SET_FIREPLACE_MODE, set_fireplace_mode)
    hass.services.async_register(DOMAIN, SERVICE_SET_COOLING_MODE, set_cooling_mode)
    hass.services.async_register(
        DOMAIN, SERVICE_SET_VENTILATION_MODE, set_ventilation_mode
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TEMPERATURE_MODE, set_temperature_mode
    )

    hass.services.async_register(
        DOMAIN, SERVICE_SET_SYSTEM_ACTIVE_MODE, set_system_active_mode
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UNLOCK_MAINTENANCE_SETTINGS, unlock_maintenance_settings
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TARGET_TEMPERATURE_NORMAL, set_target_temperature_normal
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TARGET_TEMPERATURE_COOL, set_target_temperature_cool
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TARGET_TEMPERATURE_ECONOMY, set_target_temperature_economy
    )

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
