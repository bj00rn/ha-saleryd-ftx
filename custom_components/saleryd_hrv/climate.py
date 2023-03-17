import logging

from homeassistant.components.climate import (
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, UnitOfPower
from homeassistant.helpers.entity_platform import AddEntitiesCallback

PRESET_COOL = "cool"

FAN_MODE_HOME = "home"
FAN_MODE_AWAY = "away"
FAN_MODE_BOOST = "boost"

from .const import DOMAIN
from .entity import SalerydLokeEntity

_LOGGER = logging.getLogger(__package__)


class _SalerydClimate(ClimateEntity, SalerydLokeEntity):
    """Representation of a HRV as HVAC unit."""


class SalerydVentilation(_SalerydClimate):
    """Ventilation mode"""

    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.FAN_MODE
    )
    _attr_assumed_state = True
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO, PRESET_COOL]
    _attr_fan_modes = [FAN_MODE_HOME, FAN_MODE_AWAY, FAN_MODE_BOOST]
    _attr_hvac_modes = [HVACMode.FAN_ONLY, HVACMode.COOL]
    _attr_temperature_unit = TEMP_CELSIUS

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self.hass.services.call(
            DOMAIN,
            "set_cooling_mode",
            {"value": self.hvac_modes.index(hvac_mode)},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        value = self.coordinator.data.get("MK")
        if not isinstance(value, list):
            return None
        if value[0] == 0:
            return HVACMode.FAN_ONLY
        if value[0] == 1:
            return HVACMode.COOL

    @property
    def hvac_action(self) -> HVACAction | str | None:
        value = self.coordinator.data.get("MK")
        if not isinstance(value, list):
            return None
        if value[0] == 0:
            return HVACAction.IDLE
        if value[0] == 1:
            return HVACAction.COOLING

    @property
    def preset_mode(self) -> str | None:
        """Get current preset mode"""
        if not self.coordinator.data.get("MT"):
            return None
        value = self.coordinator.data.get("MT")[0]
        return self.preset_modes[value]

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""

        self.hass.services.call(
            DOMAIN,
            "set_temperature_mode",
            {"value": self.preset_modes.index(preset_mode)},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)

    @property
    def fan_mode(self) -> str | None:
        fan_mode = self.coordinator.data.get("MF")
        if isinstance(fan_mode, list):
            return self.fan_modes[fan_mode[0]]

    def set_fan_mode(self, fan_mode: str) -> None:
        self.hass.services.call(
            DOMAIN,
            "set_ventilation_mode",
            {"value": self.fan_modes.index(fan_mode)},
            blocking=True,
            limit=10,
        )
        self.schedule_update_ha_state(force_refresh=True)

    @property
    def current_temperature(self):
        if not self.coordinator.data.get("*TC"):
            return None
        return float(self.coordinator.data.get("*TC"))


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SalerydVentilation(
            coordinator,
            entry.entry_id,
            ClimateEntityDescription(key="MF", name="Saleryd HRV"),
        ),
    ]

    async_add_entities(entities)
