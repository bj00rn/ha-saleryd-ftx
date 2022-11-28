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
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, UnitOfPower

from .const import DEFAULT_NAME, DOMAIN, ATTRIBUTION

import decimal

sensors = {
    "heat_exchanger_rpm": SensorEntityDescription(
        key="*XB",
        name="Heat exchanger rotor speed",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "heat_exchanger_speed": SensorEntityDescription(
        key="*XB",
        name="Heat exchanger rotor speed percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "supply_air_temperature": SensorEntityDescription(
        key="*TC",
        name="Supply air temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
    ),
    "heater_air_temperature": SensorEntityDescription(
        key="*TK",
        name="Heater air temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
    ),
    "heater_temperature_percent": SensorEntityDescription(
        key="*MJ",
        name="Heater temperature percent",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    "heater_power": SensorEntityDescription(
        key="MG",
        name="Heater power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    "target_temperature": SensorEntityDescription(
        key="*DT",
        name="Target temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
    ),
    "supply_fan_speed": SensorEntityDescription(
        key="*DA",
        icon="mdi:fan",
        name="Supply fan speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "extract_fan_speed": SensorEntityDescription(
        key="*DB",
        icon="mdi:fan",
        name="Extract fan speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "ventilation_mode": SensorEntityDescription(
        key="MF",
        name="Ventilation mode",
        icon="mdi:hvac",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "fireplace_mode": SensorEntityDescription(
        key="MB",
        icon="mdi:fireplace",
        name="Fireplace mode",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "temperature_mode": SensorEntityDescription(
        key="MT",
        icon="mdi:home-thermometer",
        name="Temperature mode",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "filter_months_left": SensorEntityDescription(
        key="FL",
        icon="mdi:home-thermometer",
        name="Filter months left",
        state_class=SensorStateClass.MEASUREMENT,
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
        data_type: type = decimal.Decimal,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = entity_description
        self._id = entry_id
        self._data_type = data_type

        self._attr_name = entity_description.name
        self._attr_unique_id = f"{entry_id}_{entity_description.name}"
        self._id = entry_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Saleryd",
        )

    def _translate_value(self, value):
        if self.entity_description.key == "MG":
            if value == 0:
                return 900
            elif value == 1:
                return 1800
            else:
                return None

        return value

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value:
            value = self._data_type(value[0] if isinstance(value, list) else value)
            return self._translate_value(value)

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
