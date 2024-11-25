from abc import abstractmethod
from enum import IntEnum
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import (
    CONF_VALUE,
    DOMAIN,
    SERVICE_SET_TEMPERATURE_MODE,
    SERVICE_SET_VENTILATION_MODE,
    TemperatureModeEnum,
    VentilationModeEnum,
)
from .coordinator import SalerydLokeDataUpdateCoordinator
from .data import SalerydLokeConfigEntry
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
        system_property = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key, None),
        )
        self._attr_current_option = self.OPTION_ENUM(system_property.value).name
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
    hass: HomeAssistant,
    entry: "SalerydLokeConfigEntry",
    async_add_entities: AddEntitiesCallback,
):
    coordinator = entry.runtime_data.coordinator
    entites = [
        SalerydLokeTemperatureModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(
                key=DataKeyEnum.MODE_TEMPERATURE,
                name="Temperature mode",
                icon="mdi:home-thermometer",
            ),
        ),
        SalerydLokeVentilationModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(
                DataKeyEnum.MODE_FAN, name="Ventilation mode", icon="mdi:hvac"
            ),
        ),
    ]
    async_add_entities(entites)
