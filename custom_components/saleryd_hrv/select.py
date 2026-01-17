"""Select entities for the Saleryd Loke integration."""

from abc import ABC
from enum import IntEnum
from typing import TYPE_CHECKING, Type

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import slugify
from pysaleryd.const import DataKey
from pysaleryd.data import SystemProperty

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


class SalerydLokeSelect(SalerydLokeEntity, SelectEntity, ABC):
    """Base class for Saleryd Loke select entities."""

    OPTION_ENUM_CLASS: Type[IntEnum]

    def __init__(
        self,
        coordinator: "SalerydLokeDataUpdateCoordinator",
        entry: "SalerydLokeConfigEntry",
        entity_description: SelectEntityDescription,
    ):
        self._attr_current_option = None
        self._entry = entry
        self._attr_options = [o.name for o in self.OPTION_ENUM_CLASS]
        self.entity_id = f"select.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        system_property = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key, None),
        )
        if system_property.value is not None:
            self._attr_current_option = self.OPTION_ENUM_CLASS(
                system_property.value
            ).name  # type: ignore[assignment]
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._entry.runtime_data.bridge.send_command(
            self.entity_description.key, self.OPTION_ENUM_CLASS[option]
        )


class SalerydLokeVentilationModeSelect(SalerydLokeSelect):
    """Select entity for ventilation modes."""

    OPTION_ENUM_CLASS = VentilationModeEnum


class SalerydLokeTemperatureModeSelect(SalerydLokeSelect):
    """Select entity for temperature modes."""

    OPTION_ENUM_CLASS = TemperatureModeEnum


class SalerydLokeSystemActiveModeSelect(SalerydLokeSelect):
    """Select entity for system active modes."""

    OPTION_ENUM_CLASS = ModeEnum


async def async_setup_entry(
    _hass: "HomeAssistant",
    entry: "SalerydLokeConfigEntry",
    async_add_entities: "AddEntitiesCallback",
):
    """ "Set up the Saleryd Loke select entities from a config entry."""

    coordinator = entry.runtime_data.coordinator
    entites = [
        SalerydLokeTemperatureModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(
                key=DataKey.MODE_TEMPERATURE,
                name="Temperature mode",
                icon="mdi:home-thermometer",
            ),
        ),
        SalerydLokeVentilationModeSelect(
            coordinator,
            entry,
            SelectEntityDescription(
                DataKey.MODE_FAN, name="Ventilation mode", icon="mdi:hvac"
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
                    key=DataKey.CONTROL_SYSTEM_STATE,
                    name="System active",
                    entity_category=EntityCategory.CONFIG,
                    icon="mdi:power",
                ),
            )
        ]
        async_add_entities(config_entities)
