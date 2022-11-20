"""Sensor platform for integration_blueprint."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)

from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, REVOLUTIONS_PER_MINUTE, PERCENTAGE

from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR, ATTRIBUTION

import decimal

sensors = {
    "heat_exchanger_rpm": SensorEntityDescription(
        key="*XB",
        name="Heat exchanger speed",
        device_class=None,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "heat_exchanger_speed": SensorEntityDescription(
        key="*XB",
        name="Heat exchanger speed percent",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "supply_air_temperature": SensorEntityDescription(
        key="*TC",
        name="Supply air temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    "heater_air_temperature": SensorEntityDescription(
        key="*TK",
        name="Heater air temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    "target_temperature": SensorEntityDescription(
        key="*DT",
        name="Target temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    "supply_fan_speed": SensorEntityDescription(
        key="*DA",
        name="Supply fan speed",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "extract_fan_speed": SensorEntityDescription(
        key="*DB",
        name="Extract fan speed",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "ventilation_mode": SensorEntityDescription(
        key="MF",
        name="Ventilation mode",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "fireplace_mode": SensorEntityDescription(
        key="MB",
        name="Fireplace mode",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "temperature_mode": SensorEntityDescription(
        key="MH",
        name="Temperature mode",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SalerydLokeSensor(coordinator, entry.entry_id, entity_description)
        for entity_description in sensors.values()
    ]

    async_add_entities(entities)


class SalerydLokeSensor(CoordinatorEntity, SensorEntity):
    """integration_blueprint Sensor class."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = entity_description
        self._id = entry_id

        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self._id = entry_id

        self._attr_device_info = DeviceInfo(
            configuration_url="https://dashboard.airthings.com/",
            identifiers={(DOMAIN, entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Airthings",
        )

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value:
            return decimal.Decimal(value[0] if isinstance(value, list) else value)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        state_attrs = {
            "attribution": ATTRIBUTION,
            "api": str(self.coordinator.data.get("*SC")),
            "integration": DOMAIN,
        }
        value = self.coordinator.data.get(self.entity_description.key)
        if (
            isinstance(value, list)
            and len(value) == 4
            and self.coordinator.data.get(self.entity_description.key)[3]
        ):
            state_attrs["minutes_left"]: self.coordinator.data.get(
                self.entity_description.key
            )[3]
        return state_attrs
