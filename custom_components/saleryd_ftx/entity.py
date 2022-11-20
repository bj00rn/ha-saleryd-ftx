"""SalerydLokeEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorStateClass


from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, NAME, VERSION, ATTRIBUTION


# class SalerydLokeEntity(CoordinatorEntity):
#     """Entity"""

#     def __init__(self, entity_descriptor, coordinator):
#         self._attr_name = name
#         self.config_entry = config_entry
#         self._attr_unique_id = f"{self.config_entry.entry_id}_{name}"

#         super().__init__(coordinator)

#     @property
#     def device_info(self):
#         return {
#             "identifiers": {(DOMAIN, self.config_entry.entry_id)},
# # #             "name": self.name,
#             "model": VERSION,
#             "manufacturer": NAME,
#         }
