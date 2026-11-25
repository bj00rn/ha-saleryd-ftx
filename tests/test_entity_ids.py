"""Tests for entity id generation and the cooking mode switch."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, State, valid_entity_id
from pysaleryd.const import DataKeyEnum
import pytest
from pytest_homeassistant_custom_component.common import (
    MockEntityPlatform,
    mock_restore_cache,
)

from custom_components.saleryd_hrv.const import KEY_COOKING_MODE, LOGGER, ModeEnum
from custom_components.saleryd_hrv.coordinator import SalerydLokeDataUpdateCoordinator
from custom_components.saleryd_hrv.entity import build_entity_id
from custom_components.saleryd_hrv.switch import SalerydLokeCookingModeSwitch


def _entry(unique_id="Saleryd FTX"):
    entry = MagicMock()
    entry.unique_id = unique_id
    entry.entry_id = "01TESTENTRY"
    entry.data = {}
    entry.runtime_data.bridge.send_command = AsyncMock()
    return entry


@pytest.mark.parametrize(
    ("platform", "unique_id", "name", "expected"),
    [
        (
            "select",
            "Saleryd FTX",
            "Ventilation mode",
            "select.saleryd_ftx_ventilation_mode",
        ),
        (
            "binary_sensor",
            "saleryd_ftx",
            "System active",
            "binary_sensor.saleryd_ftx_system_active",
        ),
        (
            "sensor",
            "saleryd_",
            "Fireplace mode minutes left",
            "sensor.saleryd_fireplace_mode_minutes_left",
        ),
    ],
)
def test_build_entity_id_is_valid(platform, unique_id, name, expected):
    """Entity ids are valid entity ids."""
    entity_id = build_entity_id(platform, _entry(unique_id), name)
    assert entity_id == expected
    assert valid_entity_id(entity_id)


async def _add_cooking_switch(hass: HomeAssistant, unique_id: str, is_on: bool):
    entry = _entry(unique_id)
    coordinator = SalerydLokeDataUpdateCoordinator(hass, LOGGER)
    coordinator.async_set_updated_data({})
    switch = SalerydLokeCookingModeSwitch(
        coordinator,
        entry,
        SwitchEntityDescription(key=KEY_COOKING_MODE, name="Cooking mode"),
    )
    if is_on:
        mock_restore_cache(hass, [State(switch.entity_id, STATE_ON)])
    await MockEntityPlatform(hass, domain="switch").async_add_entities([switch])
    return entry, coordinator


@pytest.mark.parametrize("unique_id", ["Saleryd FTX", "saleryd_"])
async def test_cooking_mode_cancels_fireplace_mode(hass: HomeAssistant, unique_id):
    """Cooking mode turns fireplace mode off when its timer is about to expire.

    This must work regardless of the timer sensor's entity id, which differs
    from the generated one for e.g. entries named "saleryd_" or when renamed.
    """
    entry, coordinator = await _add_cooking_switch(hass, unique_id, is_on=True)
    send_command = entry.runtime_data.bridge.send_command

    coordinator.async_set_updated_data({DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE: "10"})
    await hass.async_block_till_done()
    send_command.assert_not_called()

    coordinator.async_set_updated_data({DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE: "2"})
    await hass.async_block_till_done()
    send_command.assert_awaited_once_with(DataKeyEnum.FIREPLACE_MODE, ModeEnum.Off)

    # Unchanged timer value does not resend the command
    coordinator.async_set_updated_data({DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE: "2"})
    await hass.async_block_till_done()
    send_command.assert_awaited_once()


@pytest.mark.parametrize("minutes_left", ["0", "2"])
async def test_cooking_mode_off_or_timer_idle_does_nothing(
    hass: HomeAssistant, minutes_left
):
    """Nothing is sent when cooking mode is off, or when the timer is not running."""
    is_on = minutes_left == "0"
    entry, coordinator = await _add_cooking_switch(hass, "Saleryd FTX", is_on=is_on)

    coordinator.async_set_updated_data(
        {DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE: minutes_left}
    )
    await hass.async_block_till_done()
    entry.runtime_data.bridge.send_command.assert_not_called()
