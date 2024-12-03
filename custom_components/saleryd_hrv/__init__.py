"""
Custom integration to integrate Saleryd HRV system with Home Assistant.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

import async_timeout
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration
from homeassistant.util import slugify
from pysaleryd.client import Client

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    CONF_INSTALLER_PASSWORD,
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    CONFIG_VERSION,
    DEFAULT_NAME,
    DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS,
    DEPRECATED_CONF_MAINTENANCE_PASSWORD,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    STARTUP_MESSAGE,
)

if TYPE_CHECKING:
    from .data import SalerydLokeConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall

from .bridge import SalerydLokeBridge
from .coordinator import SalerydLokeDataUpdateCoordinator
from .data import SalerydLokeData

SCAN_INTERVAL = timedelta(seconds=30)


async def async_migrate_entry(
    hass: HomeAssistant, entry: "SalerydLokeConfigEntry"
) -> bool:
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


async def async_setup_entry(hass: HomeAssistant, entry: "SalerydLokeConfigEntry"):
    """Set up the integration from ConfigEntry."""
    integration = async_get_loaded_integration(hass, entry.domain)
    LOGGER.info(STARTUP_MESSAGE, integration.name, integration.version)

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
        coordinator = SalerydLokeDataUpdateCoordinator(hass, LOGGER)
        bridge = SalerydLokeBridge(client, coordinator, LOGGER)
        entry.runtime_data = SalerydLokeData(
            client=client,
            coordinator=coordinator,
            integration=integration,
            bridge=bridge,
        )
        await coordinator.async_config_entry_first_refresh()

        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: "SalerydLokeConfigEntry"
) -> bool:
    """Handle unload of an entry."""

    # unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # disconnect client
    client: SalerydLokeDataUpdateCoordinator = entry.runtime_data.client
    client.disconnect()

    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, entry: "SalerydLokeConfigEntry"
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
