import enum
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, UnitOfPower

from .const import DOMAIN
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    ClimateEntityDescription,
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_BOOST,
    HVACMode,
)
from .entity import SalerydLokeEntity


class _SalerydClimate(ClimateEntity, SalerydLokeEntity):
    """Representation of a HRV as fan."""


class SalerydVentilation(_SalerydClimate):
    """Ventilation mode"""

    _attr_supported_features = ClimateEntityFeature.PRESET_MODE
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, PRESET_BOOST]
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.COOL]
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_mode = HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Get current preset mode"""
        value = self.coordinator.data.get(self.entity_description.key)[0]
        if value == 0:
            return PRESET_HOME
        elif value == 1:
            return PRESET_AWAY
        elif value == 2:
            return PRESET_BOOST


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
