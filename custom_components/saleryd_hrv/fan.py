import enum
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
    FanEntityDescription,
)
from .entity import SalerydLokeEntity


class VentMode(enum.Enum):
    """State of the connection."""

    NONE = -1
    Home = 0
    Away = 1
    Boost = 2


ATTR_VENT_MODE = "vent_mode"
VENT_AWAY = VentMode.Away
VENT_HOME = VentMode.Home
VENT_BOOST = VentMode.Boost
VENT_MODES = [VENT_AWAY.name, VENT_HOME.name, VENT_BOOST.name]

DEFAULT_VENT_MODE = VENT_HOME


class SalerydFan(FanEntity, SalerydLokeEntity):
    """Representation of a HRV as fan."""

    @property
    def is_on(self) -> bool:
        """Return the current preset_mode."""
        return self.coordinator.data.get(self.entity_description.key)[0] is not None


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SalerydFan(
            coordinator,
            entry.entry_id,
            FanEntityDescription(key="MB", name="Fireplace Mode Fan"),
        ),
    ]

    async_add_entities(entities)
