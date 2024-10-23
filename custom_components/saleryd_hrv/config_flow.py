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
    DOMAIN,
    LOGGER,
    NAME,
)


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

            return await self._show_config_form("user", user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_WEBSOCKET_IP] = "192.168.1.151"
        user_input[CONF_WEBSOCKET_PORT] = 3001
        user_input[CONF_NAME] = NAME
        user_input[CONF_ENABLE_MAINTENANCE_SETTINGS] = False
        user_input[CONF_MAINTENANCE_PASSWORD] = ""

        return await self._show_config_form("user", user_input)

    async def async_step_reconfigure(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._config_entry = config_entry
        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        if not user_input:
            return await self._show_config_form(
                step_id="reconfigure_confirm", user_input={**self._config_entry.data}
            )
        return self.async_update_reload_and_abort(
            self._config_entry,
            data=user_input,
            reason="reconfigure_successful",
        )

    async def _show_config_form(
        self, step_id, user_input
    ):  # pylint: disable=unused-argument
        """Show the configuration form to edit configuration data."""
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=user_input[CONF_NAME],
                    ): str,
                    vol.Required(
                        CONF_WEBSOCKET_IP,
                        default=user_input[CONF_WEBSOCKET_IP],
                    ): str,
                    vol.Required(
                        CONF_WEBSOCKET_PORT,
                        default=user_input[CONF_WEBSOCKET_PORT],
                    ): int,
                    vol.Optional(
                        CONF_ENABLE_MAINTENANCE_SETTINGS,
                        default=user_input[CONF_ENABLE_MAINTENANCE_SETTINGS],
                    ): vol.Coerce(bool),
                    vol.Optional(
                        CONF_MAINTENANCE_PASSWORD,
                        default=user_input[CONF_MAINTENANCE_PASSWORD],
                    ): str,
                }
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
