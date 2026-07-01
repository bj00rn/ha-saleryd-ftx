"""Tests for mode repeat listener."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from pysaleryd.const import DataKeyEnum

from custom_components.saleryd_hrv.const import ModeEnum, VentilationModeEnum
from custom_components.saleryd_hrv.switch import SalerydLokeModeRepeatListener


def _event(old_state: str | None, new_state: str | None):
    old = SimpleNamespace(state=old_state) if old_state is not None else None
    new = SimpleNamespace(state=new_state) if new_state is not None else None
    return SimpleNamespace(data={"old_state": old, "new_state": new})


def _listener(repeat_count: int, command_key: DataKeyEnum, command_value: int):
    bridge = SimpleNamespace(send_command=AsyncMock())
    entry = SimpleNamespace(
        unique_id="test",
        runtime_data=SimpleNamespace(bridge=bridge),
    )
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda _: SimpleNamespace(state=str(repeat_count)))
    )
    return (
        SalerydLokeModeRepeatListener(
            hass=hass,
            entry=entry,
            mode_name="test",
            track_sensor_name="Boost mode minutes left",
            repeat_number_name="Boost mode repeats",
            command_key=command_key,
            command_value=command_value,
        ),
        bridge.send_command,
    )


async def test_mode_repeat_listener_repeats_up_to_configured_count():
    """Repeat is decremented on each extension."""
    listener, send_command = _listener(
        repeat_count=2,
        command_key=DataKeyEnum.MODE_FAN,
        command_value=VentilationModeEnum.Boost,
    )

    await listener._maybe_repeat_mode(_event("4", "3"))
    await listener._maybe_repeat_mode(_event("3", "240"))
    await listener._maybe_repeat_mode(_event("4", "3"))
    await listener._maybe_repeat_mode(_event("3", "240"))
    await listener._maybe_repeat_mode(_event("4", "3"))

    assert send_command.await_count == 2


async def test_mode_repeat_listener_does_not_repeat_when_disabled():
    """No mode extension happens when repeat is zero."""
    listener, send_command = _listener(
        repeat_count=0,
        command_key=DataKeyEnum.FIREPLACE_MODE,
        command_value=ModeEnum.On,
    )

    await listener._maybe_repeat_mode(_event("4", "3"))

    assert send_command.await_count == 0
