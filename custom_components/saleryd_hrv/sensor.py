"""Sensor platform"""

from datetime import timedelta
import logging
from typing import Any

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
from homeassistant.util import Throttle, slugify

from .const import (
    CLIENT_STATE,
    DEFAULT_NAME,
    DOMAIN,
    HEATER_MODE_HIGH,
    HEATER_MODE_LOW,
    ISSUE_URL,
    SUPPORTED_FIRMWARES,
    TEMPERATURE_MODE_COOL,
    TEMPERATURE_MODE_ECO,
    TEMPERATURE_MODE_NORMAL,
    UNSUPPORTED_FIRMWARES,
    VENTILATION_MODE_AWAY,
    VENTILATION_MODE_BOOST,
    VENTILATION_MODE_HOME,
)
from .entity import SalerydLokeEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)


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

    @Throttle(min_time=timedelta(minutes=1))
    def _log_unknown_sensor_value(self, value):
        _LOGGER.warning(
            "Unknown value [%s] for sensor [%s] [%s], feel free to file an issue with the integration at %s and provide this message.",
            value,
            self.entity_description.name,
            self.entity_description.key,
            ISSUE_URL,
        )

    @Throttle(min_time=timedelta(days=1))
    def _log_unsupported_firmware(self, version):
        """Write to logs if firmware version is unsupported"""
        _LOGGER.error(
            "Your control system version is (%s). This integration is incompatible with the following versions: %s",
            version,
            ", ".join(UNSUPPORTED_FIRMWARES),
        )

    @Throttle(min_time=timedelta(days=1))
    def _log_unknown_firmware(self, version):
        _LOGGER.warning(
            "Unknown support for your control system version (%s), feel free to file an issue with the integration at %s and provide this message. This integration has been verified to work with the following versions: %s",
            version,
            ISSUE_URL,
            ", ".join(SUPPORTED_FIRMWARES),
        )

    def _translate_value(self, value):
        if value is None:
            return value

        if self.entity_description.key == "*EB":
            return any(value)

        value = value[0] if isinstance(value, list) else value
        if self.entity_description.key == "MG":
            if value == HEATER_MODE_LOW:
                return 900
            elif value == HEATER_MODE_HIGH:
                return 1800
            else:
                self._log_unknown_sensor_value(value)

        if self.entity_description.key == "MT":
            if value == TEMPERATURE_MODE_NORMAL:
                return "Normal"
            elif value == TEMPERATURE_MODE_ECO:
                return "Eco"
            elif value == TEMPERATURE_MODE_COOL:
                return "Cool"
            else:
                self._log_unknown_sensor_value(value)

        if self.entity_description.key == "MF":
            if value == VENTILATION_MODE_HOME:
                return "Home"
            elif value == VENTILATION_MODE_AWAY:
                return "Away"
            elif value == VENTILATION_MODE_BOOST:
                return "Boost"
            else:
                self._log_unknown_sensor_value(value)

        if self.entity_description.key == "*SC":
            if value not in SUPPORTED_FIRMWARES:
                self._log_unknown_firmware(value)
            if value in UNSUPPORTED_FIRMWARES:
                self._log_unsupported_firmware(value)

        return value

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        return self._translate_value(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = {}

        value = self.coordinator.data.get(self.entity_description.key)

        if self.entity_description.key == "*EB" and isinstance(value, list):
            for error in value:
                attrs[error] = True

        if value:
            value = value[0] if isinstance(value, list) else value

        if self.entity_description.key == "MT":
            if value == TEMPERATURE_MODE_COOL:
                attrs["target_temperature"] = self.coordinator.data.get("TF")[0]
            elif value == TEMPERATURE_MODE_ECO:
                attrs["target_temperature"] = self.coordinator.data.get("TE")[0]
            elif value == TEMPERATURE_MODE_NORMAL:
                attrs["target_temperature"] = self.coordinator.data.get("TD")[0]
        elif self.entity_description.key == "MF" and value == VENTILATION_MODE_BOOST:
            attrs["minutes_left"] = self.coordinator.data.get("*FI")

        return attrs


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
    "boost_mode_minutes_left": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*FI",
            icon="mdi:wrench-clock",
            name="Boost mode minutes left",
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
        ),
    },
    "fireplace_mode_minutes_left": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*ME",
            icon="mdi:wrench-clock",
            name="Fireplace mode minutes left",
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
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
    "connection_state": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key=CLIENT_STATE,
            icon="mdi:wrench-clock",
            name="Connection state",
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
    "control_system_warning": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*EB",
            icon="mdi:alert",
            name="System warning",
            device_class=SensorDeviceClass.ENUM,
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
