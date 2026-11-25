"""Switch platform"""

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import CONF_ENABLE_INSTALLER_SETTINGS, KEY_COOKING_MODE, LOGGER, ModeEnum
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity, build_entity_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
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
