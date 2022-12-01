"""Adds config flow for SalerydLoke."""
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.const import CONF_NAME
import voluptuous as vol

from .gateway import Gateway
from .const import (
    CONF_WEBSOCKET_PORT,
    CONF_WEBSOCKET_IP,
    DOMAIN,
    PLATFORMS,
    MANUFACTURER,
)


class SalerydLokeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SalerydLoke."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_connection(
                user_input[CONF_WEBSOCKET_IP], user_input[CONF_WEBSOCKET_PORT]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                self._errors["base"] = "connect"

            return await self._show_config_form(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_WEBSOCKET_IP] = "192.168.1.151"
        user_input[CONF_WEBSOCKET_PORT] = 3001
        user_input[CONF_NAME] = MANUFACTURER

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SalerydLokeOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
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
                }
            ),
            errors=self._errors,
        )

    async def _test_connection(self, ip, port):
        """Return true if connection is working"""
        try:
            session = async_create_clientsession(self.hass)
            gateway = Gateway(session, ip, port)
            data = await gateway.send_command("CV", "")
            if data:
                return True
        except Exception as e:  # pylint: disable=broad-except
            pass
        return False


class SalerydLokeOptionsFlowHandler(config_entries.OptionsFlow):
    """SalerydLoke config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_NAME), data=self.options
        )
