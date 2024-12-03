from enum import IntEnum
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    ModeEnum,
    TemperatureModeEnum,
    VentilationModeEnum,
)
from .coordinator import SalerydLokeDataUpdateCoordinator
from .entity import SalerydLokeEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import SalerydLokeConfigEntry


class SalerydLokeSelect(SalerydLokeEntity, SelectEntity):
    OPTION_ENUM: IntEnum = None

    def __init__(
        self,
        coordinator: "SalerydLokeDataUpdateCoordinator",
        entry: "SalerydLokeConfigEntry",
        entity_description: SelectEntityDescription,
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
        if system_property.value is not None:
            self._attr_current_option = self.OPTION_ENUM(system_property.value).name
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._entry.runtime_data.bridge.send_command(
            self.entity_description.key, self.OPTION_ENUM[option]
        )


class SalerydLokeVentilationModeSelect(SalerydLokeSelect):
    OPTION_ENUM = VentilationModeEnum


class SalerydLokeTemperatureModeSelect(SalerydLokeSelect):
    OPTION_ENUM = TemperatureModeEnum


class SalerydLokeSystemActiveModeSelect(SalerydLokeSelect):
    OPTION_ENUM = ModeEnum


async def async_setup_entry(
    hass: "HomeAssistant",
    entry: "SalerydLokeConfigEntry",
    async_add_entities: "AddEntitiesCallback",
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

    if entry.data.get(CONF_ENABLE_INSTALLER_SETTINGS):
        config_entities = [
            SalerydLokeSystemActiveModeSelect(
                coordinator,
                entry,
                SelectEntityDescription(
                    key=DataKeyEnum.CONTROL_SYSTEM_STATE,
                    name="System active",
                    entity_category=EntityCategory.CONFIG,
                    icon="mdi:power",
                ),
            )
        ]
        async_add_entities(config_entities)
