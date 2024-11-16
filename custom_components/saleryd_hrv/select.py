from abc import abstractmethod
from enum import IntEnum
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    CONF_VALUE,
    DOMAIN,
    SERVICE_SET_TEMPERATURE_MODE,
    SERVICE_SET_VENTILATION_MODE,
    TemperatureModeEnum,
    VentilationModeEnum,
)
from .coordinator import SalerydLokeDataUpdateCoordinator
from .entity import SalerydLokeEntity


class SalerydLokeSelect(SalerydLokeEntity, SelectEntity):
    SERVICE: str = None
    OPTION_ENUM: IntEnum = None

    def __init__(
        self, coordinator: SalerydLokeDataUpdateCoordinator, entry, entity_description
    ):
        self._attr_current_option = None
        self._entry = entry
        self._attr_options = [o.name for o in self.OPTION_ENUM]
        self.entity_id = f"select.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_option = self.OPTION_ENUM(
            self.coordinator.data[self.entity_description.key][0]
        ).name
        super()._handle_coordinator_update()

    def select_option(self, option) -> None:
        """Change the selected option."""
        self.hass.services.call(
            DOMAIN,
            self.SERVICE,
            {CONF_DEVICE: self.device_entry.id, CONF_VALUE: self.OPTION_ENUM[option]},
            blocking=True,
        )


class SalerydLokeVentilationModeSelect(SalerydLokeSelect):
    SERVICE = SERVICE_SET_VENTILATION_MODE
    OPTION_ENUM = VentilationModeEnum


class SalerydLokeTemperatureModeSelect(SalerydLokeSelect):
    SERVICE = SERVICE_SET_TEMPERATURE_MODE
    OPTION_ENUM = TemperatureModeEnum


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = entry.runtime_data
    entites = [
        SalerydLokeTemperatureModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(
                key="MT", name="Temperature mode", icon="mdi:home-thermometer"
            ),
        ),
        SalerydLokeVentilationModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(key="MF", name="Ventilation mode", icon="mdi:hvac"),
        ),
    ]
    async_add_entities(entites)
