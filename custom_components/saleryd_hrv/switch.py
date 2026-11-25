"""Switch platform"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_ON
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    DOMAIN,
    KEY_COOKING_MODE,
    LOGGER,
    ModeEnum,
    VentilationModeEnum,
)
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity, build_entity_id

if TYPE_CHECKING:
    from homeassistant.core import CALLBACK_TYPE, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SalerydLokeDataUpdateCoordinator
    from .data import SalerydLokeConfigEntry


class SalerydLokeVirtualSwitch(SaleryLokeVirtualEntity, SwitchEntity):
    """Virtual switch base class"""

    def __init__(
        self, coordinator, entry: "SalerydLokeConfigEntry", entity_description
    ) -> None:
        self._entry = entry
        self._attr_is_on = False
        self.entity_id = build_entity_id("switch", entry, entity_description.name)
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
        self.entity_id = build_entity_id("switch", entry, entity_description.name)
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
        self._coordinator: "SalerydLokeDataUpdateCoordinator" = coordinator
        self._minutes_left: int | None = None
        super().__init__(coordinator, entry, entity_description)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._attr_is_on = state is not None and state.state == STATE_ON
        # Follow the fireplace timer through the coordinator rather than the
        # timer sensor's entity id, which the user may have renamed.
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        minutes_left = SystemProperty.from_str(
            DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE,
            self._coordinator.data.get(DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE),
        ).value
        if minutes_left == self._minutes_left:
            return
        self._minutes_left = minutes_left
        if not self._attr_is_on or not isinstance(minutes_left, int):
            return
        # 0 means the timer is not running
        if 0 < minutes_left < self.THRESHOLD:
            LOGGER.info("Cooking mode triggered deactivation of fireplace mode")
            LOGGER.debug(
                "Cooking mode deactivating fireplace mode, since time left [%s] < threshold [%s]",
                minutes_left,
                self.THRESHOLD,
            )
            self.hass.async_create_task(
                self._entry.runtime_data.bridge.send_command(
                    DataKeyEnum.FIREPLACE_MODE, ModeEnum.Off
                )
            )


class SalerydLokeModeRepeatListener:
    """Repeat a mode activation when its timer is about to expire."""

    THRESHOLD = 3

    def __init__(
        self,
        hass: "HomeAssistant",
        entry: "SalerydLokeConfigEntry",
        mode_name: str,
        minutes_left_key: DataKeyEnum,
        repeat_number_name: str,
        command_key: DataKeyEnum,
        command_value: int,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._mode_name = mode_name
        self._minutes_left_key = minutes_left_key
        self._repeat_unique_id = f"{entry.unique_id}_{slugify(repeat_number_name)}"
        self._command_key = command_key
        self._command_value = command_value
        self._unsubscribe: "CALLBACK_TYPE | None" = None
        self._active = False
        self._remaining_repeats = 0
        self._extension_pending = False

    def async_start(self) -> "CALLBACK_TYPE":
        self._unsubscribe = self._entry.runtime_data.coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        return self.async_stop

    def async_stop(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _get_configured_repeats(self) -> int:
        # Resolve through the registry so renamed entities keep working
        entity_id = er.async_get(self.hass).async_get_entity_id(
            "number", DOMAIN, self._repeat_unique_id
        )
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is None:
            return 0
        try:
            return max(0, int(float(state.state)))
        except ValueError:
            return 0

    @callback
    def _handle_coordinator_update(self) -> None:
        minutes_left = SystemProperty.from_str(
            self._minutes_left_key,
            self._entry.runtime_data.coordinator.data.get(self._minutes_left_key),
        ).value
        if not isinstance(minutes_left, (int, float)):
            # Unknown value, keep state until the timer is reported again
            return

        if minutes_left <= 0:
            self._active = False
            self._extension_pending = False
            return

        if not self._active:
            self._active = True
            if not self._extension_pending:
                self._remaining_repeats = self._get_configured_repeats()

        if minutes_left > self.THRESHOLD:
            # Timer was reset (or a new session started)
            self._extension_pending = False
            return

        if self._extension_pending or self._remaining_repeats <= 0:
            return

        if self._get_configured_repeats() <= 0:
            return

        self._remaining_repeats -= 1
        self._extension_pending = True
        LOGGER.info("Extending %s timer by repeating mode activation", self._mode_name)
        LOGGER.debug(
            "Extending %s mode since time left [%s] <= threshold [%s], repeats left [%s]",
            self._mode_name,
            minutes_left,
            self.THRESHOLD,
            self._remaining_repeats,
        )
        self.hass.async_create_task(
            self._entry.runtime_data.bridge.send_command(
                self._command_key, self._command_value
            )
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
            minutes_left_key=DataKeyEnum.MINUTES_LEFT_BOOST_MODE,
            repeat_number_name="Boost mode repeats",
            command_key=DataKeyEnum.MODE_FAN,
            command_value=VentilationModeEnum.Boost,
        ),
        SalerydLokeModeRepeatListener(
            hass=hass,
            entry=entry,
            mode_name="fireplace",
            minutes_left_key=DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE,
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
