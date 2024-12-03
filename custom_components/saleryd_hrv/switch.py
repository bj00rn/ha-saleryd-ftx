"""Switch platform"""

from typing import TYPE_CHECKING, Any, Coroutine

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HassJobType
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import KEY_COOKING_MODE, LOGGER, ModeEnum
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity

if TYPE_CHECKING:
    from homeassistant.core import Event, EventStateChangedData, HomeAssistant
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


class SalerydLokeCookingModeSwitch(SalerydLokeVirtualSwitch):
    """Emulate virtual cooking mode switch to deactivate fireplace mode before timer expires."""

    THRESHOLD = 3

    def __init__(self, coordinator, entry, entity_description) -> None:
        self._unsubscribe = None
        super().__init__(coordinator, entry, entity_description)

    async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
        track_entity_id = (
            f"sensor.{self._entry.unique_id}_{slugify('Fireplace mode minutes left')}"
        )
        self._attr_is_on = False
        self._unsubscribe = async_track_state_change_event(
            self.hass,
            track_entity_id,
            self._maybe_cancel,
            HassJobType.Coroutinefunction,
        )
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> Coroutine[Any, Any, None]:
        if self._unsubscribe:
            self._unsubscribe()
        await super().async_will_remove_from_hass()

    async def _maybe_cancel(self, event: "Event[EventStateChangedData]"):
        if self._attr_is_on:
            if not event.data["new_state"].state.isnumeric():
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
