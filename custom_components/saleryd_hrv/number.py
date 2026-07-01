from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import SystemProperty

from .const import (
    CONF_ENABLE_INSTALLER_SETTINGS,
    KEY_BOOST_MODE_REPEAT,
    KEY_FIREPLACE_MODE_REPEAT,
)
from .entity import SalerydLokeEntity, SaleryLokeVirtualEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SalerydLokeDataUpdateCoordinator
    from .data import SalerydLokeConfigEntry


class SalerydLokeNumber(SalerydLokeEntity, NumberEntity):

    def __init__(
        self,
        coordinator: "SalerydLokeDataUpdateCoordinator",
        entry: "SalerydLokeConfigEntry",
        entity_description: "NumberEntityDescription",
    ) -> None:

        self._attr_mode = NumberMode.BOX
        self._entry = entry

        """Initialize the sensor."""
        self.entity_id = f"number.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    def _get_native_value(self, system_property: SystemProperty):
        return system_property.value

    @property
    def native_value(self):
        system_property = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key),
        )
        return self._get_native_value(system_property)

    async def async_set_native_value(self, value):
        await self._entry.runtime_data.bridge.send_command(
            self.entity_description.key, int(value)
        )


class SalerydLokeVirtualNumber(SaleryLokeVirtualEntity, NumberEntity, RestoreEntity):
    def __init__(self, entry, entity_description: "NumberEntityDescription") -> None:
        self._attr_mode = NumberMode.BOX
        self._attr_native_value = 0
        self.entity_id = f"number.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(entry, entity_description)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is None:
            return
        try:
            self._attr_native_value = max(0, int(float(state.state)))
        except ValueError:
            return

    async def async_set_native_value(self, value):
        self._attr_native_value = int(value)
        self.async_write_ha_state()


async def async_setup_entry(
    hass: "HomeAssistant",
    entry: "SalerydLokeConfigEntry",
    async_add_entities: "AddEntitiesCallback",
):
    coordinator = entry.runtime_data.coordinator
    config_entities = [
        SalerydLokeVirtualNumber(
            entry,
            NumberEntityDescription(
                key=KEY_BOOST_MODE_REPEAT,
                name="Boost mode repeats",
                native_max_value=10,
                native_min_value=0,
                native_step=1,
                icon="mdi:repeat",
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        SalerydLokeVirtualNumber(
            entry,
            NumberEntityDescription(
                key=KEY_FIREPLACE_MODE_REPEAT,
                name="Fireplace mode repeats",
                native_max_value=10,
                native_min_value=0,
                native_step=1,
                icon="mdi:repeat",
                entity_category=EntityCategory.CONFIG,
            ),
        ),
    ]

    if entry.data.get(CONF_ENABLE_INSTALLER_SETTINGS):
        config_entities.extend(
            [
                SalerydLokeNumber(
                    coordinator,
                    entry,
                    NumberEntityDescription(
                        key=DataKeyEnum.BOOST_MODE_MINUTES,
                        name="Boost mode minutes",
                        device_class=NumberDeviceClass.DURATION,
                        native_unit_of_measurement=UnitOfTime.MINUTES,
                        native_max_value=240,
                        native_min_value=5,
                        icon="mdi:fan-clock",
                        entity_category=EntityCategory.CONFIG,
                    ),
                ),
                SalerydLokeNumber(
                    coordinator,
                    entry,
                    NumberEntityDescription(
                        key=DataKeyEnum.FIREPLACE_MODE_MINUTES,
                        name="Fireplace mode minutes",
                        device_class=NumberDeviceClass.DURATION,
                        native_unit_of_measurement=UnitOfTime.MINUTES,
                        native_max_value=30,
                        native_min_value=15,
                        icon="mdi:fan-clock",
                        entity_category=EntityCategory.CONFIG,
                    ),
                ),
                SalerydLokeNumber(
                    coordinator,
                    entry,
                    NumberEntityDescription(
                        key=DataKeyEnum.TARGET_TEMPERATURE_NORMAL,
                        name="Normal temperature",
                        device_class=NumberDeviceClass.TEMPERATURE,
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        native_max_value=30,
                        native_min_value=10,
                        icon="mdi:home-thermometer",
                        entity_category=EntityCategory.CONFIG,
                    ),
                ),
                SalerydLokeNumber(
                    coordinator,
                    entry,
                    NumberEntityDescription(
                        key=DataKeyEnum.TARGET_TEMPERATURE_ECONOMY,
                        name="Economy temperature",
                        device_class=NumberDeviceClass.TEMPERATURE,
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        native_max_value=30,
                        native_min_value=10,
                        icon="mdi:home-thermometer",
                        entity_category=EntityCategory.CONFIG,
                    ),
                ),
                SalerydLokeNumber(
                    coordinator,
                    entry,
                    NumberEntityDescription(
                        key=DataKeyEnum.TARGET_TEMPERATURE_COOL,
                        name="Cool temperature",
                        device_class=NumberDeviceClass.TEMPERATURE,
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        native_max_value=30,
                        native_min_value=10,
                        icon="mdi:home-thermometer",
                        entity_category=EntityCategory.CONFIG,
                    ),
                ),
            ]
        )

    async_add_entities(config_entities)
