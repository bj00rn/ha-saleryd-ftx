"""Sensor platform"""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from .const import DEFAULT_NAME, DOMAIN
from .entity import SalerydLokeEntity


class SalerydLokeSensor(SalerydLokeEntity, SensorEntity):
    """Sensor base class."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = f"sensor.${DEFAULT_NAME}_${slugify(entity_description.name)}"

        super().__init__(coordinator, entry_id, entity_description)

    def _translate_value(self, value):
        if self.entity_description.key == "MG":
            if value == 0:
                return 900
            elif value == 1:
                return 1800

        if self.entity_description.key == "MT":
            if value == 0:
                return "Comfort"
            elif value == 1:
                return "Eco"
            elif value == 2:
                return "Cool"

        if self.entity_description.key == "MF":
            if value == 0:
                return "Home"
            elif value == 1:
                return "Away"
            elif value == 2:
                return "Boost"

        return value

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value:
            value = value[0] if isinstance(value, list) else value
            return self._translate_value(value)


sensors = {
    "heat_exchanger_rpm": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*XB",
            name="Heat exchanger rotor speed",
            native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            icon="mdi:cog-transfer",
            state_class=SensorStateClass.MEASUREMENT,
        ),
    },
    "heat_exchanger_speed": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*XA",
            name="Heat exchanger rotor speed percent",
            icon="mdi:cog-transfer",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    },
    "supply_air_temperature": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*TC",
            name="Supply air temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    },
    "heater_air_temperature": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*TK",
            name="Heater air temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    },
    "heater_temperature_percent": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*MJ",
            icon="mdi:heating-coil",
            name="Heater temperature percent",
            device_class=SensorDeviceClass.POWER_FACTOR,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
        ),
    },
    "heater_power": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="MG",
            icon="mdi:fuse-blade",
            name="Heater power",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.WATT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    },
    "supply_fan_speed": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*DA",
            icon="mdi:fan-speed-1",
            name="Supply fan speed",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    },
    "extract_fan_speed": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*DB",
            icon="mdi:fan-speed-2",
            name="Extract fan speed",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    },
    "ventilation_mode": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="MF",
            name="Ventilation mode",
            icon="mdi:hvac",
            device_class=SensorDeviceClass.ENUM,
        ),
    },
    "temperature_mode": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="MT",
            icon="mdi:home-thermometer",
            name="Temperature mode",
            device_class=SensorDeviceClass.ENUM,
        ),
    },
    "filter_months_left": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*FL",
            icon="mdi:wrench-clock",
            name="Filter months left",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=UnitOfTime.MONTHS,
        ),
    },
    "control_system_name": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*SB",
            icon="mdi:barcode",
            name="System name",
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    },
    "prod_nr": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*SA",
            icon="mdi:barcode",
            name="Product number",
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    },
    "control_system_version": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*SC",
            icon="mdi:wrench-clock",
            name="System version",
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    },
}


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        sensor.get("klass")(coordinator, entry.entry_id, sensor.get("description"))
        for sensor in sensors.values()
    ]

    async_add_entities(entities)
