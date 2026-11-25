"""Tests for connection timeouts."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_NAME
from homeassistant.exceptions import ConfigEntryNotReady
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.saleryd_hrv import async_setup_entry
from custom_components.saleryd_hrv.config_flow import SalerydLokeFlowHandler
from custom_components.saleryd_hrv.const import (
    CONF_WEBSOCKET_IP,
    CONF_WEBSOCKET_PORT,
    DOMAIN,
)


async def wait_forever(*args):
    """Wait until cancelled by the timeout."""
    await asyncio.Event().wait()


async def test_homeassistant_fixture(hass):
    """The test plugin provides a Home Assistant instance and config entries."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert hass.config_entries.async_get_entry(entry.entry_id) is entry


@pytest.mark.asyncio
async def test_setup_connection_timeout():
    """A connection timeout disconnects the client and defers setup."""
    entry = MagicMock()
    entry.data = {CONF_WEBSOCKET_IP: "127.0.0.1", CONF_WEBSOCKET_PORT: 3001}
    client = MagicMock()
    client.connect = AsyncMock(side_effect=wait_forever)
    timeout = asyncio.timeout

    with (
        patch("custom_components.saleryd_hrv.async_get_loaded_integration"),
        patch("custom_components.saleryd_hrv.async_create_clientsession"),
        patch("custom_components.saleryd_hrv.Client", return_value=client),
        patch("asyncio.timeout", side_effect=lambda delay: timeout(0)) as mock_timeout,
        pytest.raises(ConfigEntryNotReady, match="Timeout while connecting"),
    ):
        await async_setup_entry(MagicMock(), entry)

    mock_timeout.assert_called_once_with(10)
    client.disconnect.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["user", "reconfigure_confirm"])
async def test_flow_connection_timeout(step):
    """Both configuration flows report a connection timeout."""
    flow = SalerydLokeFlowHandler()
    flow._test_connection = AsyncMock(side_effect=wait_forever)
    flow.async_show_form = MagicMock(return_value={"errors": {"base": "connect"}})
    user_input = {CONF_WEBSOCKET_IP: "127.0.0.1", CONF_WEBSOCKET_PORT: 3001}
    timeout = asyncio.timeout

    with patch("asyncio.timeout", side_effect=lambda delay: timeout(0)) as mock_timeout:
        result = await getattr(flow, f"async_step_{step}")(user_input)

    mock_timeout.assert_called_once_with(10)
    assert result["errors"] == {"base": "connect"}
    assert flow.async_show_form.call_args.kwargs["errors"] == {"base": "connect"}


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["user", "reconfigure_confirm"])
async def test_flow_connection_success(step):
    """Both configuration flows accept a successful connection."""
    flow = SalerydLokeFlowHandler()
    flow._test_connection = AsyncMock(return_value=True)
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_update_reload_and_abort = MagicMock(return_value={"type": "abort"})
    flow._config_entry = MagicMock(data={CONF_NAME: "Existing"})
    user_input = {
        CONF_NAME: "Device",
        CONF_WEBSOCKET_IP: "127.0.0.1",
        CONF_WEBSOCKET_PORT: 3001,
    }

    result = await getattr(flow, f"async_step_{step}")(user_input)

    flow._test_connection.assert_awaited_once_with("127.0.0.1", 3001)
    if step == "user":
        assert result["type"] == "create_entry"
        flow.async_create_entry.assert_called_once_with(title="Device", data=user_input)
    else:
        assert result["type"] == "abort"
        flow.async_update_reload_and_abort.assert_called_once_with(
            flow._config_entry, data=user_input, reason="reconfigure_successful"
        )
