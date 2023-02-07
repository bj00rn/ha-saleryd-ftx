"""Adds config flow for SalerydLoke."""
import logging
import asyncio

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.const import CONF_NAME
import voluptuous as vol

from pysaleryd.client import Client
from .const import (
    CONF_WEBSOCKET_PORT,
    CONF_WEBSOCKET_IP,
    DOMAIN,
    NAME,
)


_LOGGER: logging.Logger = logging.getLogger(__package__)


class SalerydLokeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SalerydLoke."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

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
        user_input[CONF_NAME] = NAME

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit configuration data."""
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

        async def connected(client: Client):
            """Is client connected"""
            while True:
                await asyncio.sleep(1)
                if client.connected():
                    return True

        try:
            session = async_create_clientsession(self.hass)
            client = Client(ip, port, session)
            await asyncio.wait_for(connected(client), 10)
            return True
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Could not connect", exc_info=True)
            pass

        return False


#     @staticmethod
#     @callback
#     def async_get_options_flow(config_entry):
#         return SalerydLokeOptionsFlowHandler(config_entry)


# class SalerydLokeOptionsFlowHandler(config_entries.OptionsFlow):
#     """SalerydLoke config flow options handler."""

#     def __init__(self, config_entry):
#         self.config_entry = config_entry

#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         errors: Dict[str, str] = {}

#         if user_input is not None:
#             if not errors:
#                 return self.async_create_entry(title="", data=user_input)

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(
#                         CONF_WEBSOCKET_IP,
#                         default=self.config_entry.data.get(CONF_WEBSOCKET_IP),
#                     ): str,
#                     vol.Required(
#                         CONF_WEBSOCKET_PORT,
#                         default=self.config_entry.data.get(CONF_WEBSOCKET_PORT),
#                     ): int,
#                 }
#             ),
#             # data_schema=vol.Schema(
#             #     {
#             #         vol.Required(x, default=self.options.get(x, True)): bool
#             #         for x in sorted(PLATFORMS)
#             #     }
#             # ),
#         )
