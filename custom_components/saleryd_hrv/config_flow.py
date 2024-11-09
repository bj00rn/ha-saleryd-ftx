"""Adds config flow for SalerydLoke."""

from __future__ import annotations

from typing import Any, Mapping

import async_timeout
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from pysaleryd.client import Client
import voluptuous as vol

from .const import (
    CONF_ENABLE_MAINTENANCE_SETTINGS,
    CONF_MAINTENANCE_PASSWORD,
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    CONFIG_VERSION,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
)

RECONFIG_DATA = {
    vol.Required(CONF_WEBSOCKET_IP): str,
    vol.Required(CONF_WEBSOCKET_PORT): int,
    vol.Optional(CONF_ENABLE_MAINTENANCE_SETTINGS): vol.Coerce(bool),
    vol.Optional(CONF_MAINTENANCE_PASSWORD): str,
}

CONFIG_DATA = {
    vol.Required(CONF_NAME): str,
    **RECONFIG_DATA,
}

CONFIG_SCHEMA = vol.Schema({**CONFIG_DATA})
RECONFIG_SCHEMA = vol.Schema({**RECONFIG_DATA})


class SalerydLokeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SalerydLoke."""

    VERSION = CONFIG_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    _config_entry: config_entries.ConfigEntry

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Comment the next 2 lines if multiple instances of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                async with async_timeout.timeout(10):
                    await self._test_connection(
                        user_input[CONF_WEBSOCKET_IP], user_input[CONF_WEBSOCKET_PORT]
                    )
            except TimeoutError:
                self._errors["base"] = "connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    CONFIG_SCHEMA, user_input
                ),
                errors=self._errors,
            )
        else:
            suggested_values = {
                CONF_NAME: DEFAULT_NAME,
                CONF_WEBSOCKET_IP: "192.168.1.151",
                CONF_WEBSOCKET_PORT: 3001,
                CONF_ENABLE_MAINTENANCE_SETTINGS: False,
                CONF_MAINTENANCE_PASSWORD: "",
            }

            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    CONFIG_SCHEMA, suggested_values
                ),
                errors=self._errors,
            )

    async def async_step_reconfigure(
        self, user_input: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._config_entry = config_entry
        return await self.async_step_reconfigure_confirm(user_input)

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            try:
                async with async_timeout.timeout(10):
                    await self._test_connection(
                        user_input[CONF_WEBSOCKET_IP], user_input[CONF_WEBSOCKET_PORT]
                    )
            except TimeoutError:
                self._errors["base"] = "connect"
            else:
                new_data = self._config_entry.data.copy()
                new_data |= {**user_input}
                return self.async_update_reload_and_abort(
                    self._config_entry,
                    data=new_data,
                    reason="reconfigure_successful",
                )

            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    RECONFIG_SCHEMA, user_input
                ),
                errors=self._errors,
            )
        else:
            return self.async_show_form(
                data_schema=self.add_suggested_values_to_schema(
                    RECONFIG_SCHEMA, self._config_entry.data
                ),
                errors=self._errors,
            )

    async def _test_connection(self, ip, port):
        """Return true if connection is working"""
        try:
            async with Client(ip, port, async_create_clientsession(self.hass)):
                return True
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error("Could not connect", exc_info=True)
            raise e
