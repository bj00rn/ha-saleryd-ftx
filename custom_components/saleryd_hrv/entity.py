"""Entity"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, MANUFACTURER
from .coordinator import SalerydLokeDataUpdateCoordinator


class SaleryLokeVirtualEntity(Entity):
    """Virtual Entity base class"""

    def __init__(
        self,
        entry: ConfigEntry,
        entity_description: EntityDescription,
    ) -> None:
        self.entity_description = entity_description
        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry.unique_id}_{slugify(entity_description.name)}"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, entry.unique_id)
            },
            name=entry.data.get(CONF_NAME),
            manufacturer=MANUFACTURER,
        )


class SalerydLokeEntity(CoordinatorEntity):
    """Entity base class"""

    def __init__(
        self,
        coordinator: SalerydLokeDataUpdateCoordinator,
        entry: ConfigEntry,
        entity_description: EntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = entity_description
        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry.unique_id}_{slugify(entity_description.name)}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, entry.unique_id)
            },
            name=entry.data.get(CONF_NAME),
            manufacturer=MANUFACTURER,
        )
