"""Switch platform"""
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.util import slugify

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    VENTILATION_MODE_AWAY,
    VENTILATION_MODE_BOOST,
    VENTILATION_MODE_HOME,
)
from .entity import SalerydLokeEntity


class SalerydLokeBinarySwitch(SalerydLokeEntity, SwitchEntity):
    """Switch base class."""

    _state_when_on = 1
    _state_when_off = 0
    _service_turn_on = ""
    _service_turn_off = ""
    _can_expire = False
    _expire_key = None

    def __init__(self, coordinator, entry_id, entity_description) -> None:
        self.entity_id = f"switch.${DEFAULT_NAME}_${slugify(entity_description.name)}"
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
        self.schedule_update_ha_state(force_refresh=True)

    def turn_off(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            self._service_turn_off,
            {"value": self._state_when_off},
            blocking=True,
        )
        self.schedule_update_ha_state(force_refresh=True)

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


class SalerydLokeFireplaceModeBinarySwitch(SalerydLokeBinarySwitch):
    """Fireplace mode switch class."""

    _service_turn_on = "set_fireplace_mode"
    _service_turn_off = "set_fireplace_mode"
    _can_expire = True
    _expire_key = "*ME"


class SalerydLokeCoolingModeBinarySwitch(SalerydLokeBinarySwitch):
    """Cooling switch class."""

    _service_turn_on = "set_cooling_mode"
    _service_turn_off = "set_cooling_mode"


class SalerydLokeVentilationModeBinarySwitch(SalerydLokeBinarySwitch):
    """Cooling switch class."""

    _service_turn_on = "set_ventilation_mode"
    _service_turn_off = "set_ventilation_mode"


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
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        switch.get("klass")(coordinator, entry.entry_id, switch.get("description"))
        for switch in switches.values()
    ]

    async_add_entities(entities)
