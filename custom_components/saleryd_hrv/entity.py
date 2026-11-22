"""Entity"""

from homeassistant.config_entries import TYPE_CHECKING
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, MANUFACTURER
from .coordinator import SalerydLokeDataUpdateCoordinator

if TYPE_CHECKING:
    from .data import SalerydLokeConfigEntry


def build_entity_id(platform: str, entry: "SalerydLokeConfigEntry", name: str) -> str:
    """Build a valid entity_id from the config entry unique id and entity name.

    The config entry unique id is the user supplied name (e.g. "Saleryd FTX"),
    so it must be slugified to produce a valid entity_id. The result matches
    the entity_id Home Assistant already derived from the unslugified value,
    so existing installations keep their entity ids.
    """
    return f"{platform}.{slugify(entry.unique_id)}_{slugify(name)}"


class SaleryLokeVirtualEntity(Entity):
    """Virtual Entity base class"""

    def __init__(
        self,
        entry: "SalerydLokeConfigEntry",
        entity_description: EntityDescription,
    ) -> None:
        self.entity_description = entity_description
        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry.unique_id}_{slugify(entity_description.name)}"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_NAME),
            manufacturer=MANUFACTURER,
        )


class SalerydLokeEntity(CoordinatorEntity):
    """Entity base class"""

    def __init__(
        self,
        coordinator: SalerydLokeDataUpdateCoordinator,
        entry: "SalerydLokeConfigEntry",
        entity_description: EntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = entity_description
        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry.entry_id}_{slugify(entity_description.name)}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_NAME),
            manufacturer=MANUFACTURER,
        )

    def get_value(self):
        return self.coordinator.data.get(self.entity_description.key, None)
