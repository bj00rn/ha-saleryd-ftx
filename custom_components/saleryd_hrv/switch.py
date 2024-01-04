"""Switch platform"""
from typing import Any, Coroutine

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    KEY_COOKING_MODE,
    MODE_OFF,
    MODE_ON,
    SERVICE_SET_COOLING_MODE,
    SERVICE_SET_FIREPLACE_MODE,
    SERVICE_SET_VENTILATION_MODE,
    VENTILATION_MODE_AWAY,
    VENTILATION_MODE_BOOST,
    VENTILATION_MODE_HOME,
)
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity


class SalerydLokeVirtualSwitch(SaleryLokeVirtualEntity, SwitchEntity):
    """Virtual switch base class"""

    def __init__(self, coordinator, entry_id, entity_description) -> None:
        self._attr_is_on = False
        self.entity_id = f"switch.{DEFAULT_NAME}_{slugify(entity_description.name)}"
        super().__init__(entry_id, entity_description)

    def turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.schedule_update_ha_state()


class SalerydLokeBinarySwitch(SalerydLokeEntity, SwitchEntity):
    """Switch base class."""

    _state_when_on = MODE_ON
    _state_when_off = MODE_OFF
    _service_turn_on = ""
    _service_turn_off = ""
    _can_expire = False
    _expire_key = None

    def __init__(self, coordinator, entry_id, entity_description) -> None:
        self.entity_id = f"switch.{DEFAULT_NAME}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry_id, entity_description)

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
            {"value": self._state_when_on},
            blocking=True,
        )
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            self._service_turn_off,
            {"value": self._state_when_off},
            blocking=True,
        )
        self.schedule_update_ha_state()

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

    def __init__(self, coordinator, entry_id, entity_description) -> None:
        self.unsubscribe = None
        super().__init__(coordinator, entry_id, entity_description)

    async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
        track_entity_id = (
            f"sensor.{DEFAULT_NAME}_{slugify('Fireplace mode minutes left')}"
        )
        self._attr_is_on = False
        self.unsubscribe = async_track_state_change_event(
            self.hass, track_entity_id, self._maybe_cancel
        )
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> Coroutine[Any, Any, None]:
        if self.unsubscribe:
            self.unsubscribe()
        await super().async_will_remove_from_hass()

    def _maybe_cancel(self, event):
        if self._attr_is_on:
            if not event.data["new_state"].state.isnumeric():
                return
            if float(event.data["new_state"].state) < 3:
                self.hass.services.call(
                    DOMAIN,
                    SERVICE_SET_FIREPLACE_MODE,
                    {"value": MODE_OFF},
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

    _state_when_on = VENTILATION_MODE_HOME
    _state_when_off = VENTILATION_MODE_AWAY


class SalerydLokeAwayModeBinarySwitch(SalerydLokeVentilationModeBinarySwitch):
    """Away mode switch"""

    _state_when_on = VENTILATION_MODE_AWAY
    _state_when_off = VENTILATION_MODE_HOME


class SalerydLokeBoostModeBinarySwitch(SalerydLokeVentilationModeBinarySwitch):
    """Boost mode switch"""

    _state_when_on = VENTILATION_MODE_BOOST
    _state_when_off = VENTILATION_MODE_HOME
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


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        switch.get("klass")(coordinator, entry.entry_id, switch.get("description"))
        for switch in switches.values()
    ]

    async_add_entities(entities)
