import logging

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, UnitOfPower

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    ClimateEntityDescription,
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_BOOST,
    HVACMode,
)


FAN_MODE_AUTO = "auto"
FAN_MODE_FIREPLACE = "fireplace"

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
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, PRESET_BOOST]
    _attr_fan_modes = [FAN_MODE_AUTO, FAN_MODE_FIREPLACE]
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.COOL]
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_mode = HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Get current preset mode"""
        value = self.coordinator.data.get("MF")[0]
        return self.preset_modes[value]

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""

        self.hass.services.call(
            DOMAIN,
            "set_ventilation_mode",
            {"value": self.preset_modes.index(preset_mode)},
            blocking=True,
            limit=10,
        )

    @property
    def fan_mode(self) -> str | None:
        value = self.coordinator.data.get("MB")[0]
        if value == 0:
            return FAN_MODE_AUTO
        if value == 1:
            return FAN_MODE_FIREPLACE

    def set_fan_mode(self, fan_mode: str) -> None:
        self.hass.services.call(
            DOMAIN,
            "set_fireplace_mode",
            {"value": self.fan_modes.index(fan_mode)},
            blocking=True,
            limit=10,
        )


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SalerydVentilation(
            coordinator,
            entry.entry_id,
            ClimateEntityDescription(key="MF", name="Ventilation Preset"),
        ),
    ]

    async_add_entities(entities)
