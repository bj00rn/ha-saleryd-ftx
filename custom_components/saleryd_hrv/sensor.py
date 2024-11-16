"""Sensor platform"""

from datetime import timedelta
from enum import Enum
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import Throttle, slugify

from .const import (
    ISSUE_URL,
    KEY_CLIENT_STATE,
    KEY_TARGET_TEMPERATURE,
    LOGGER,
    SUPPORTED_FIRMWARES,
    UNSUPPORTED_FIRMWARES,
    HeaterModeEnum,
    ModeEnum,
    SystemActiveModeEnum,
    TemperatureModeEnum,
    VentilationModeEnum,
)
from .entity import SalerydLokeEntity


class SalerydLokeEnumSensor(SalerydLokeEntity, SensorEntity):

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        entity_description: SensorEntityDescription,
        state_enum: Enum = ModeEnum,
    ) -> None:
        """Initialize the sensor."""
        self._state_enum = state_enum
        self._attr_options = [option.name for option in self._state_enum]
        self._attr_device_class = SensorDeviceClass.ENUM
        self.entity_id = f"sensor.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)[0]
        return self._state_enum(value).name


class SalerydLokeSensor(SalerydLokeEntity, SensorEntity):
    """Sensor base class."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = f"sensor.{entry.unique_id}_{slugify(entity_description.name)}"

        super().__init__(coordinator, entry, entity_description)

    @Throttle(min_time=timedelta(minutes=1))
    def _log_unknown_sensor_value(self, value):
        LOGGER.warning(
            "Unknown value [%s] for sensor [%s] [%s], feel free to file an issue with the integration at %s and provide this message.",
            value,
            self.entity_description.name,
            self.entity_description.key,
            ISSUE_URL,
        )

    @Throttle(min_time=timedelta(days=1))
    def _log_unsupported_firmware(self, version):
        """Write to logs if firmware version is unsupported"""
        LOGGER.error(
            "Your control system version is (%s). This integration is incompatible with the following versions: %s",
            version,
            ", ".join(UNSUPPORTED_FIRMWARES),
        )

    @Throttle(min_time=timedelta(days=1))
    def _log_unknown_firmware(self, version):
        LOGGER.warning(
            "Unknown support for your control system version (%s), feel free to file an issue with the integration at %s and provide this message. This integration has been verified to work with the following versions: %s",
            version,
            ISSUE_URL,
            ", ".join(SUPPORTED_FIRMWARES),
        )

    def _translate_value(self, value):
        if self.entity_description.key == KEY_TARGET_TEMPERATURE:
            try:
                temperature_mode = self.coordinator.data.get("MT")[0]
                if temperature_mode == TemperatureModeEnum.Cool:
                    return self.coordinator.data.get("TF")[0]
                elif temperature_mode == TemperatureModeEnum.Economy:
                    return self.coordinator.data.get("TE")[0]
                elif temperature_mode == TemperatureModeEnum.Normal:
                    return self.coordinator.data.get("TD")[0]
            except TypeError as exc:
                LOGGER.debug(exc)

        if value is None:
            return value

        if self.entity_description.key == "*EB":
            return any(value)

        value = value[0] if isinstance(value, list) else value

        if self.entity_description.key in ["*ME", "*FI"] and not value:
            # return None if time left is 0
            return None

        if self.entity_description.key == "MG":
            heater_percent = self.coordinator.data.get("*MJ") / 100
            if value == HeaterModeEnum.Low:
                return heater_percent * 900
            elif value == HeaterModeEnum.High:
                return heater_percent * 1800
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
            try:
                if value == TemperatureModeEnum.Cool:
                    attrs["target_temperature"] = self.coordinator.data.get("TF")[0]
                elif value == TemperatureModeEnum.Economy:
                    attrs["target_temperature"] = self.coordinator.data.get("TE")[0]
                elif value == TemperatureModeEnum.Normal:
                    attrs["target_temperature"] = self.coordinator.data.get("TD")[0]
            except TypeError as exc:
                LOGGER.debug(exc)
        elif self.entity_description.key == "MF" and value == VentilationModeEnum.Boost:
            minutes_left = self.coordinator.data.get("*FI")
            if minutes_left:
                attrs["minutes_left"] = minutes_left

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
    "heater_power_percent": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key="*MJ",
            icon="mdi:heating-coil",
            name="Heater power percent",
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
            suggested_display_precision=0,
            native_unit_of_measurement=UnitOfPower.WATT,
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
    "target_temperature": {
        "klass": SalerydLokeSensor,
        "description": SensorEntityDescription(
            key=KEY_TARGET_TEMPERATURE,
            icon="mdi:home-thermometer",
            name="Target temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
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
            key=KEY_CLIENT_STATE,
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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup sensor platform."""
    coordinator = entry.runtime_data

    entities = [
        sensor.get("klass")(coordinator, entry, sensor.get("description"))
        for sensor in sensors.values()
    ]

    enum_sensors = [
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            SensorEntityDescription(
                key="MT",
                icon="mdi:home-thermometer",
                name="Temperature mode",
            ),
            state_enum=TemperatureModeEnum,
        ),
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            SensorEntityDescription(
                key="MH",
                icon="mdi:heating-coil",
                name="Heater active",
            ),
        ),
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            SensorEntityDescription(
                key="MP",
                icon="mdi:power",
                name="System active",
            ),
            SystemActiveModeEnum,
        ),
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key="MF",
                name="Ventilation mode",
                icon="mdi:hvac",
            ),
            state_enum=VentilationModeEnum,
        ),
    ]

    async_add_entities(entities)
    async_add_entities(enum_sensors)
