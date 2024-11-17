"""Switch platform"""

from typing import Any, Coroutine

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import (
    CONF_VALUE,
    DOMAIN,
    KEY_COOKING_MODE,
    LOGGER,
    SERVICE_SET_COOLING_MODE,
    SERVICE_SET_FIREPLACE_MODE,
    SERVICE_SET_VENTILATION_MODE,
    ModeEnum,
    VentilationModeEnum,
)
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity


class SalerydLokeVirtualSwitch(SaleryLokeVirtualEntity, SwitchEntity):
    """Virtual switch base class"""

    def __init__(self, coordinator, entry: ConfigEntry, entity_description) -> None:
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

    _state_when_on = ModeEnum.On
    _state_when_off = ModeEnum.Off
    _service_turn_on = ""
    _service_turn_off = ""
    _can_expire = False
    _expire_key = None

    def __init__(self, coordinator, entry: ConfigEntry, entity_description) -> None:
        self.entity_id = f"switch.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    @property
    def is_on(self):
        """Return true if the switch is on."""
        value = self.coordinator.data.get(self.entity_description.key)
        if isinstance(value, list):
            return value[0] == self._state_when_on

    def turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            self._service_turn_on,
            {CONF_DEVICE: self.device_entry.id, CONF_VALUE: self._state_when_on},
            blocking=True,
        )

    def turn_off(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            self._service_turn_off,
            {CONF_DEVICE: self.device_entry.id, CONF_VALUE: self._state_when_off},
            blocking=True,
        )

    @property
    def extra_state_attributes(self):
        if (
            self._can_expire
            and self._expire_key
            and self.coordinator.data.get(self._expire_key)
        ):
            attrs = {"minutes_left": self.coordinator.data.get(self._expire_key)}
            return attrs
        return None


class SalerydLokeCookingModeSwitch(SalerydLokeVirtualSwitch):
    """Emulate virtual cooking mode switch to deactivate fireplace mode before timer expires."""

    THRESHOLD = 3

    def __init__(self, coordinator, entry: ConfigEntry, entity_description) -> None:
        self._unsubscribe = None
        super().__init__(coordinator, entry, entity_description)

    async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
        track_entity_id = (
            f"sensor.{self._entry.unique_id}_{slugify('Fireplace mode minutes left')}"
        )
        self._attr_is_on = False
        self._unsubscribe = async_track_state_change_event(
            self.hass, track_entity_id, self._maybe_cancel
        )
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> Coroutine[Any, Any, None]:
        if self._unsubscribe:
            self._unsubscribe()
        await super().async_will_remove_from_hass()

    def _maybe_cancel(self, event):
        if self._attr_is_on:
            if not event.data["new_state"].state.isnumeric():
                return
            if float(event.data["new_state"].state) < self.THRESHOLD:
                LOGGER.debug(
                    "Deactivating fireplace mode, since time left [%s] < threshold [%s]",
                    event.data["new_state"].state,
                    self.THRESHOLD,
                )

                self.hass.services.call(
                    DOMAIN,
                    SERVICE_SET_FIREPLACE_MODE,
                    {CONF_DEVICE: self.device_entry.id, CONF_VALUE: ModeEnum.Off},
                    blocking=True,
                )


class SalerydLokeFireplaceModeBinarySwitch(SalerydLokeBinarySwitch):
    """Fireplace mode switch class."""

    _service_turn_on = SERVICE_SET_FIREPLACE_MODE
    _service_turn_off = SERVICE_SET_FIREPLACE_MODE
    _can_expire = True
    _expire_key = "*ME"


class SalerydLokeCoolingModeBinarySwitch(SalerydLokeBinarySwitch):
    """Cooling switch class."""

    _service_turn_on = SERVICE_SET_COOLING_MODE
    _service_turn_off = SERVICE_SET_COOLING_MODE


class SalerydLokeVentilationModeBinarySwitch(SalerydLokeBinarySwitch):
    """Ventilation mode switch class."""

    _service_turn_on = SERVICE_SET_VENTILATION_MODE
    _service_turn_off = SERVICE_SET_VENTILATION_MODE


class SalerydLokeHomeModeBinarySwitch(SalerydLokeVentilationModeBinarySwitch):
    """Home mode switch"""

    _state_when_on = VentilationModeEnum.Home
    _state_when_off = VentilationModeEnum.Away


class SalerydLokeAwayModeBinarySwitch(SalerydLokeVentilationModeBinarySwitch):
    """Away mode switch"""

    _state_when_on = VentilationModeEnum.Away
    _state_when_off = VentilationModeEnum.Home


class SalerydLokeBoostModeBinarySwitch(SalerydLokeVentilationModeBinarySwitch):
    """Boost mode switch"""

    _state_when_on = VentilationModeEnum.Boost
    _state_when_off = VentilationModeEnum.Home
    _can_expire = True
    _expire_key = "*FI"


switches = {
    "fireplace_mode": {
        "klass": SalerydLokeFireplaceModeBinarySwitch,
        "description": SwitchEntityDescription(
            key="MB",
            icon="mdi:fireplace",
            name="Fireplace mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
    "cooling_mode": {
        "klass": SalerydLokeCoolingModeBinarySwitch,
        "description": SwitchEntityDescription(
            key="MK",
            icon="mdi:snowflake",
            name="Cooling mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
    "home_mode": {
        "klass": SalerydLokeHomeModeBinarySwitch,
        "description": SwitchEntityDescription(
            key="MF",
            icon="mdi:home",
            name="Home mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
    "away_mode": {
        "klass": SalerydLokeAwayModeBinarySwitch,
        "description": SwitchEntityDescription(
            key="MF",
            icon="mdi:exit-run",
            name="Away mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
    "boost_mode": {
        "klass": SalerydLokeBoostModeBinarySwitch,
        "description": SwitchEntityDescription(
            key="MF",
            icon="mdi:fan",
            name="Boost mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
    "cooking_mode": {
        "klass": SalerydLokeCookingModeSwitch,
        "description": SwitchEntityDescription(
            key=KEY_COOKING_MODE,
            icon="mdi:stove",
            name="Cooking mode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Setup sensor platform."""
    coordinator = entry.runtime_data

    entities = [
        switch.get("klass")(coordinator, entry, switch.get("description"))
        for switch in switches.values()
    ]

    async_add_entities(entities)
