"""Switch platform for integration_blueprint."""
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass,
)

from .const import DOMAIN
from .entity import SalerydLokeEntity


class SalerydLokeBinarySwitch(SalerydLokeEntity, SwitchEntity):
    """integration_blueprint switch class."""

    @property
    def is_on(self):
        """Return true if the switch is on."""
        value = self.coordinator.data.get(self.entity_description.key)
        if isinstance(value, list):
            return value[0] == 1


class SalerydLokeFireplaceModeBinarySwitch(SalerydLokeBinarySwitch):
    """integration_blueprint switch class."""

    def turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            "set_fireplace_mode",
            {"value": 1},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)

    def turn_off(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            "set_fireplace_mode",
            {"value": 0},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)


class SalerydLokeCoolingModeBinarySwitch(SalerydLokeBinarySwitch):
    """integration_blueprint switch class."""

    def turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            "set_cooling_mode",
            {"value": 1},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)

    def turn_off(self, **kwargs) -> None:
        """Turn on the switch."""
        self.hass.services.call(
            DOMAIN,
            "set_cooling_mode",
            {"value": 0},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)


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
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        switch.get("klass")(coordinator, entry.entry_id, switch.get("description"))
        for switch in switches.values()
    ]

    async_add_entities(entities)
