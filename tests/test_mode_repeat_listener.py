"""Tests for mode repeat listener."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from pysaleryd.const import DataKeyEnum

from custom_components.saleryd_hrv import switch as switch_module
from custom_components.saleryd_hrv.const import ModeEnum, VentilationModeEnum
from custom_components.saleryd_hrv.switch import SalerydLokeModeRepeatListener


class _Harness:
    def __init__(self, monkeypatch, repeats, key, command_key, command_value):
        self.repeats = repeats
        self.key = key
        self.send_command = AsyncMock()
        self.tasks = []
        self.data = {}
        entry = SimpleNamespace(
            unique_id="test",
            runtime_data=SimpleNamespace(
                bridge=SimpleNamespace(send_command=self.send_command),
                coordinator=SimpleNamespace(data=self.data),
            ),
        )

        def create_task(coro):
            self.tasks.append(coro)

        hass = SimpleNamespace(
            async_create_task=create_task,
            states=SimpleNamespace(
                get=lambda entity_id: (
                    SimpleNamespace(state=str(self.repeats))
                    if entity_id == "number.renamed_repeats"
                    else None
                )
            ),
        )
        registry = MagicMock()
        registry.async_get_entity_id.side_effect = lambda platform, domain, uid: (
            "number.renamed_repeats" if uid == "test_test_repeats" else None
        )
        monkeypatch.setattr(switch_module.er, "async_get", lambda _: registry)
        self.listener = SalerydLokeModeRepeatListener(
            hass=hass,
            entry=entry,
            mode_name="test",
            minutes_left_key=key,
            repeat_number_name="Test repeats",
            command_key=command_key,
            command_value=command_value,
        )

    async def feed(self, minutes):
        self.data[self.key] = minutes
        self.listener._handle_coordinator_update()
        while self.tasks:
            await self.tasks.pop()


def _boost(monkeypatch, repeats):
    return _Harness(
        monkeypatch,
        repeats,
        DataKeyEnum.MINUTES_LEFT_BOOST_MODE,
        DataKeyEnum.MODE_FAN,
        VentilationModeEnum.Boost,
    )


async def test_repeats_up_to_configured_count_across_sessions(monkeypatch):
    h = _boost(monkeypatch, 2)
    for _ in range(2):
        await h.feed(240)
        await h.feed(4)
        await h.feed(3)
        await h.feed(240)
        await h.feed(3)
        await h.feed(240)
        await h.feed(3)  # budget exhausted
        await h.feed(0)
    assert h.send_command.await_count == 4


async def test_no_duplicate_extension_while_pending(monkeypatch):
    h = _boost(monkeypatch, 3)
    await h.feed(4)
    await h.feed(3)
    await h.feed(None)
    await h.feed(2)
    assert h.send_command.await_count == 1


async def test_disabling_mid_session_stops_extensions(monkeypatch):
    h = _boost(monkeypatch, 2)
    await h.feed(240)
    h.repeats = 0
    await h.feed(3)
    assert h.send_command.await_count == 0


async def test_does_not_repeat_when_disabled(monkeypatch):
    h = _Harness(
        monkeypatch,
        0,
        DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE,
        DataKeyEnum.FIREPLACE_MODE,
        ModeEnum.On,
    )
    await h.feed(4)
    await h.feed(3)
    assert h.send_command.await_count == 0
