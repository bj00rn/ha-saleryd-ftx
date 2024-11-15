"""
Custom integration to integrate Saleryd HRV system with Home Assistant.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

import async_timeout
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_DEVICE, CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_integration
from homeassistant.util import slugify
from pysaleryd.client import Client

type SalerydLokeConfigurationEntry = ConfigEntry[SalerydLokeDataUpdateCoordinator]

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    CONF_INSTALLER_PASSWORD,
    CONF_VALUE,
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    CONFIG_VERSION,
    DEFAULT_NAME,
    DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS,
    DEPRECATED_CONF_MAINTENANCE_PASSWORD,
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
        LOGGER.error(
            "Downgrading from version %s to %s is not allowed",
            CONFIG_VERSION,
            entry.version,
        )
        return False

    if entry.version is None or entry.version < 2:
        new_data = entry.data.copy()
        new_data |= {
            CONF_ENABLE_INSTALLER_SETTINGS: False,
            CONF_INSTALLER_PASSWORD: None,
        }

        LOGGER.info("Upgrading entry to version 2")
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)

    if entry.version is None or entry.version < 3:
        unique_id = slugify(entry.data.get(CONF_NAME, DEFAULT_NAME))
        LOGGER.info("Upgrading entry to version 3, setting unique_id to %s", unique_id)
        hass.config_entries.async_update_entry(
            entry,
            version=3,
            unique_id=unique_id,
        )

    if entry.version is None or entry.version < 4:
        new_data = entry.data.copy()
        new_data[CONF_ENABLE_INSTALLER_SETTINGS] = new_data.pop(
            DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS
        )
        if DEPRECATED_CONF_MAINTENANCE_PASSWORD in new_data:
            new_data[CONF_INSTALLER_PASSWORD] = new_data.pop(
                DEPRECATED_CONF_MAINTENANCE_PASSWORD
            )

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            version=4,
        )

    return True


def _get_entry_from_service_data(
    hass: HomeAssistant, call: ServiceCall
) -> SalerydLokeDataUpdateCoordinator:
    """Return coordinator for entry id."""
    device_id = call.get(CONF_DEVICE)
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Cannot find device {device_id} is not found")
    if device.disabled:
        raise HomeAssistantError(f"Device {device_id} is disabled")

    entry = hass.config_entries.async_get_entry(device.primary_config_entry)
    if entry is None or entry.state is not ConfigEntryState.LOADED:
        raise HomeAssistantError(
            f"Config entry for device {device_id} is not found or not loaded"
        )
    return entry


def setup_hass_services(hass: HomeAssistant) -> None:
    """Register ingegration services."""

    async def control_request(call: ServiceCall, key, installer_setting=False):
        """Helper for system control calls"""
        entry = _get_entry_from_service_data(hass, call.data)
        value = call.data.get(CONF_VALUE)
        device = call.data.get(CONF_DEVICE)
        coordinator: SalerydLokeDataUpdateCoordinator = entry.runtime_data
        if installer_setting:
            installer_settings_enabled = entry.data.get(CONF_ENABLE_INSTALLER_SETTINGS)
            if not installer_settings_enabled:
                raise HomeAssistantError(
                    f"Installer settings not enabled for device {device}"
                )
            installer_password = entry.data.get(CONF_INSTALLER_PASSWORD)
            LOGGER.debug("Sending unlock installer settings control request")
            await coordinator.client.send_command("IP", installer_password)

        LOGGER.debug("Sending control request %s with payload %s", key, value)
        await coordinator.client.send_command(key, value)

    async def set_fireplace_mode(call: ServiceCall):
        """Set fireplace mode"""
        await control_request(call, "MB")

    async def set_ventilation_mode(call: ServiceCall):
        """Set ventilation mode"""
        await control_request(call, "MF")

    async def set_temperature_mode(call: ServiceCall):
        """Set temperature mode"""
        await control_request(call, "MT")

    async def set_cooling_mode(call: ServiceCall):
        """Set cooling mode"""
        await control_request(call, "MK")

    async def set_system_active_mode(call: ServiceCall):
        """Set system active mode"""
        await control_request(call, "MP", True)

    async def set_target_temperature_cool(call: ServiceCall):
        """Set target temperature for Cool temperature mode"""
        await control_request(call, "TF", True)

    async def set_target_temperature_normal(call: ServiceCall):
        """Set target temperature for Normal temperature mode"""
        await control_request(call, "TD", True)

    async def set_target_temperature_economy(call: ServiceCall):
        """Set target temperature for Economy temperature mode"""
        await control_request(call, "TE", True)

    services = {
        SERVICE_SET_FIREPLACE_MODE: set_fireplace_mode,
        SERVICE_SET_COOLING_MODE: set_cooling_mode,
        SERVICE_SET_VENTILATION_MODE: set_ventilation_mode,
        SERVICE_SET_TEMPERATURE_MODE: set_temperature_mode,
    }

    installer_services = {
        SERVICE_SET_SYSTEM_ACTIVE_MODE: set_system_active_mode,
        SERVICE_SET_TARGET_TEMPERATURE_COOL: set_target_temperature_cool,
        SERVICE_SET_TARGET_TEMPERATURE_ECONOMY: set_target_temperature_economy,
        SERVICE_SET_TARGET_TEMPERATURE_NORMAL: set_target_temperature_normal,
    }

    # register services
    for key, fn in (services | installer_services).items():
        if hass.services.has_service(DOMAIN, key):
            continue
        hass.services.async_register(DOMAIN, key, fn)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from ConfigEntry."""

    integration = await async_get_integration(hass, DOMAIN)
    LOGGER.info(STARTUP_MESSAGE, integration.name, integration.version)
    setup_hass_services(hass)

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
        entry.runtime_data = coordinator

        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unload of an entry."""

    # unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # disconnect client
    coordinator: SalerydLokeDataUpdateCoordinator = entry.runtime_data
    coordinator.client.disconnect()

    # remove services

    loaded_entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if len(loaded_entries) == 1:
        # If this is the last loaded instance, deregister any services
        # defined during integration setup:

        for key in hass.services.async_services().get(DOMAIN, dict()):
            hass.services.async_remove(DOMAIN, key)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
