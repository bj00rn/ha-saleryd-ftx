"""Switch platform"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HassJobType
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    KEY_COOKING_MODE,
    LOGGER,
    ModeEnum,
    VentilationModeEnum,
)
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity

if TYPE_CHECKING:
    from homeassistant.core import (
        CALLBACK_TYPE,
        Event,
        EventStateChangedData,
        HomeAssistant,
    )
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import SalerydLokeConfigEntry


class SalerydLokeVirtualSwitch(SaleryLokeVirtualEntity, SwitchEntity):
    """Virtual switch base class"""

    def __init__(
        self, coordinator, entry: "SalerydLokeConfigEntry", entity_description
    ) -> None:
        self._entry = entry
        self._attr_is_on = False
        self.entity_id = f"switch.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(entry, entity_description)

    def turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.schedule_update_ha_state()


class SalerydLokeBinarySwitch(SalerydLokeEntity, SwitchEntity):
    """Switch base class."""

    def __init__(
        self,
        coordinator,
        entry: "SalerydLokeConfigEntry",
        entity_description,
        state_when_on=ModeEnum.On,
        state_when_off=ModeEnum.Off,
    ) -> None:
        self._entry = entry
        self._state_when_on = state_when_on
        self._state_when_off = state_when_off
        self.entity_id = f"switch.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    @property
    def is_on(self):
        """Return true if the switch is on."""
        system_property = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key, None),
        )

        return system_property.value == self._state_when_on

    async def async_turn_on(self, **kwargs):
        await self._entry.runtime_data.bridge.send_command(
            self.entity_description.key, self._state_when_on
        )

    async def async_turn_off(self, **kwargs):
        await self._entry.runtime_data.bridge.send_command(
            self.entity_description.key, self._state_when_off
        )


class SalerydLokeCookingModeSwitch(SalerydLokeVirtualSwitch, RestoreEntity):
    """Emulate virtual cooking mode switch to deactivate fireplace mode before timer expires."""

    THRESHOLD = 3

    def __init__(self, coordinator, entry, entity_description) -> None:
        self._unsubscribe: CALLBACK_TYPE | None = None
        super().__init__(coordinator, entry, entity_description)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._attr_is_on = state is not None and state.state == STATE_ON
        track_entity_id = (
            f"sensor.{self._entry.unique_id}_{slugify('Fireplace mode minutes left')}"
        )

        self._unsubscribe = async_track_state_change_event(
            self.hass,
            track_entity_id,
            self._maybe_cancel,
            HassJobType.Coroutinefunction,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
        await super().async_will_remove_from_hass()

    async def _maybe_cancel(self, event: "Event[EventStateChangedData]"):
        if self._attr_is_on:
            if (
                event.data["new_state"] is None
                or not event.data["new_state"].state.isnumeric()
            ):
                return
            if float(event.data["new_state"].state) < self.THRESHOLD:
                LOGGER.info("Cooking mode triggered deactivation of fireplace mode")
                LOGGER.debug(
                    "Cooking mode deactivating fireplace mode, since time left [%s] < threshold [%s]",
                    event.data["new_state"].state,
                    self.THRESHOLD,
                )
                await self._entry.runtime_data.bridge.send_command(
                    DataKeyEnum.FIREPLACE_MODE, ModeEnum.Off
                )


class SalerydLokeModeRepeatListener:
    """Listen for expiring mode timers and repeat mode activations."""

    THRESHOLD = 3

    def __init__(
        self,
        hass: "HomeAssistant",
        entry: "SalerydLokeConfigEntry",
        mode_name: str,
        track_sensor_name: str,
        repeat_number_name: str,
        command_key: DataKeyEnum,
        command_value: int,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._mode_name = mode_name
        self._track_entity_id = f"sensor.{entry.unique_id}_{slugify(track_sensor_name)}"
        self._repeat_entity_id = (
            f"number.{entry.unique_id}_{slugify(repeat_number_name)}"
        )
        self._command_key = command_key
        self._command_value = command_value
        self._unsubscribe: CALLBACK_TYPE | None = None
        self._remaining_repeats: int | None = None
        self._waiting_for_reset = False

    def async_start(self) -> CALLBACK_TYPE:
        self._unsubscribe = async_track_state_change_event(
            self.hass,
            self._track_entity_id,
            self._maybe_repeat_mode,
            HassJobType.Coroutinefunction,
        )
        return self.async_stop

    def async_stop(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _parse_minutes(self, state) -> float | None:
        if state is None or not state.state.replace(".", "", 1).isnumeric():
            return None
        return float(state.state)

    def _get_configured_repeats(self) -> int:
        state = self.hass.states.get(self._repeat_entity_id)
        if state is None:
            return 0
        try:
            return max(0, int(float(state.state)))
        except ValueError:
            return 0

    async def _maybe_repeat_mode(self, event: "Event[EventStateChangedData]") -> None:
        new_minutes = self._parse_minutes(event.data.get("new_state"))
        old_minutes = self._parse_minutes(event.data.get("old_state"))
        configured_repeats = self._get_configured_repeats()

        if (
            new_minutes is not None
            and old_minutes is not None
            and new_minutes > old_minutes
        ):
            if self._waiting_for_reset:
                self._waiting_for_reset = False
            else:
                self._remaining_repeats = configured_repeats

        if self._remaining_repeats is None:
            self._remaining_repeats = configured_repeats

        if new_minutes is None or new_minutes > self.THRESHOLD:
            return

        if old_minutes is not None and old_minutes <= self.THRESHOLD:
            return

        if self._remaining_repeats <= 0:
            return

        self._remaining_repeats -= 1
        self._waiting_for_reset = True
        LOGGER.info("Extending %s timer by repeating mode activation", self._mode_name)
        LOGGER.debug(
            "Extending %s mode since time left [%s] <= threshold [%s], repeats left [%s]",
            self._mode_name,
            new_minutes,
            self.THRESHOLD,
            self._remaining_repeats,
        )
        await self._entry.runtime_data.bridge.send_command(
            self._command_key, self._command_value
        )


async def async_setup_entry(
    hass: "HomeAssistant",
    entry: "SalerydLokeConfigEntry",
    async_add_entities: "AddEntitiesCallback",
):
    """Setup sensor platform."""
    coordinator = entry.runtime_data.coordinator

    switches = [
        # "fireplace_mode"
        SalerydLokeBinarySwitch(
            coordinator,
            entry,
            entity_description=SwitchEntityDescription(
                key=DataKeyEnum.FIREPLACE_MODE,
                icon="mdi:fireplace",
                name="Fireplace mode",
                device_class=SwitchDeviceClass.SWITCH,
            ),
        ),
        # "cooling_mode"
        SalerydLokeBinarySwitch(
            coordinator,
            entry,
            entity_description=SwitchEntityDescription(
                key=DataKeyEnum.COOLING_MODE,
                icon="mdi:snowflake",
                name="Cooling mode",
                device_class=SwitchDeviceClass.SWITCH,
            ),
        ),
        # "cooking_mode"
        SalerydLokeCookingModeSwitch(
            coordinator,
            entry,
            entity_description=SwitchEntityDescription(
                key=KEY_COOKING_MODE,
                icon="mdi:stove",
                name="Cooking mode",
                device_class=SwitchDeviceClass.SWITCH,
            ),
        ),
    ]

    async_add_entities(switches)
    repeat_listeners = [
        SalerydLokeModeRepeatListener(
            hass=hass,
            entry=entry,
            mode_name="boost",
            track_sensor_name="Boost mode minutes left",
            repeat_number_name="Boost mode repeats",
            command_key=DataKeyEnum.MODE_FAN,
            command_value=VentilationModeEnum.Boost,
        ),
        SalerydLokeModeRepeatListener(
            hass=hass,
            entry=entry,
            mode_name="fireplace",
            track_sensor_name="Fireplace mode minutes left",
            repeat_number_name="Fireplace mode repeats",
            command_key=DataKeyEnum.FIREPLACE_MODE,
            command_value=ModeEnum.On,
        ),
    ]
    for listener in repeat_listeners:
        entry.async_on_unload(listener.async_start())

    if entry.data.get(CONF_ENABLE_INSTALLER_SETTINGS):
        config_entities = [
            SalerydLokeBinarySwitch(
                coordinator,
                entry,
                entity_description=SwitchEntityDescription(
                    key=DataKeyEnum.MODE_HEATER,
                    icon="mdi:heating-coil",
                    name="Heater active",
                    device_class=SwitchDeviceClass.SWITCH,
                ),
            )
        ]
        async_add_entities(config_entities)
