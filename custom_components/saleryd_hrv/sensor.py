"""Sensor platform"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import ErrorSystemProperty, SystemProperty

from .const import (
    KEY_CLIENT_STATE,
    HeaterModeEnum,
    HeaterPowerEnum,
    ModeEnum,
    SystemActiveModeEnum,
    TemperatureModeEnum,
    VentilationModeEnum,
)
from .entity import SalerydLokeEntity

if TYPE_CHECKING:
    from .coordinator import SalerydLokeDataUpdateCoordinator
    from .data import SalerydLokeConfigEntry


class SalerydLokeSensor(SalerydLokeEntity, SensorEntity):
    """Sensor base class."""

    def __init__(
        self,
        coordinator: SalerydLokeDataUpdateCoordinator,
        entry: "SalerydLokeConfigEntry",
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = f"sensor.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(coordinator, entry, entity_description)

    def _get_native_value(self, system_property: SystemProperty):
        return system_property.value

    @property
    def native_value(self):
        value = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key),
        )
        return self._get_native_value(value)

    def _get_extra_state_attributes(
        self, system_property: SystemProperty
    ) -> dict[str, Any] | None:
        return None

    @property
    def extra_state_attributes(self):
        value = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key),
        )
        return self._get_extra_state_attributes(value)


class SalerydLokeEstimatedHeaterPowerSensor(SalerydLokeSensor):

    def _get_native_value(self, heater_power_percent: SystemProperty):
        heater_power_rating = SystemProperty.from_str(
            DataKeyEnum.MODE_HEATER_POWER_RATING,
            self.coordinator.data.get(DataKeyEnum.MODE_HEATER_POWER_RATING, None),
        )

        if heater_power_percent.value is not None:
            if heater_power_rating.value == HeaterModeEnum.Low:
                return heater_power_percent.value / 100 * HeaterPowerEnum.Low
            if heater_power_rating == HeaterPowerEnum.High:
                return heater_power_percent.value / 100 * HeaterPowerEnum.High

        return None


class SalerydLokeHeaterPowerRatingSensor(SalerydLokeSensor):

    def _get_native_value(self, system_property):
        if system_property.value == HeaterModeEnum.Low:
            return HeaterPowerEnum.Low
        if system_property.value == HeaterModeEnum.High:
            return HeaterPowerEnum.High

        return None


class SalerydLokeTargetTemperatureSensor(SalerydLokeSensor):
    """Target temperature sensor"""

    def _get_native_value(self, ventilation_mode: SystemProperty):
        if ventilation_mode.value is None:
            return None

        if ventilation_mode.value == TemperatureModeEnum.Normal:
            key = DataKeyEnum.TARGET_TEMPERATURE_NORMAL
        elif ventilation_mode.value == TemperatureModeEnum.Economy:
            key = DataKeyEnum.TARGET_TEMPERATURE_ECONOMY
        elif ventilation_mode.value == TemperatureModeEnum.Cool:
            key = DataKeyEnum.TARGET_TEMPERATURE_COOL

        return SystemProperty.from_str(
            self.entity_description.key, self.coordinator.data.get(key, None)
        ).value


class SalerydLokeMinutesLeftSensor(SalerydLokeSensor):
    """Minutes left sensor"""

    def _get_native_value(self, system_property):
        if system_property.value == 0:
            # treat 0 as None
            return None
        return system_property.value


class SalerydLokeEnumSensor(SalerydLokeSensor):
    """Enum sensor"""

    def __init__(
        self,
        coordinator: SalerydLokeDataUpdateCoordinator,
        entry: "SalerydLokeConfigEntry",
        entity_description: SensorEntityDescription,
        options_enum: IntEnum = ModeEnum,
    ) -> None:
        self.options_enum = options_enum
        super().__init__(coordinator, entry, entity_description)

    def _get_native_value(self, system_property):
        if system_property.value is None:
            return None

        return self.options_enum(system_property.value).name

    @property
    def options(self):
        return [o.name for o in self.options_enum]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: "SalerydLokeConfigEntry",
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensor platform."""
    coordinator = entry.runtime_data.coordinator
    sensors = [
        # heat_exchanger_rpm
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.HEAT_EXCHANGER_ROTOR_RPM,
                name="Heat exchanger rotor speed",
                native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                icon="mdi:cog-transfer",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        ),
        # heat_exchanger_speed
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.HEAT_EXCHANGER_ROTOR_PERCENT,
                name="Heat exchanger rotor speed percent",
                icon="mdi:cog-transfer",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        ),
        # supply_air_temperature
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.AIR_TEMPERATURE_SUPPLY,
                name="Supply air temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            ),
        ),
        # heater_air_temperature
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.AIR_TEMPERATURE_AT_HEATER,
                name="Heater air temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            ),
        ),
        # heater_power_percent
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.HEATER_POWER_PERCENT,
                icon="mdi:heating-coil",
                name="Heater power percent",
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=PERCENTAGE,
            ),
        ),
        # heater_power
        SalerydLokeEstimatedHeaterPowerSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.HEATER_POWER_PERCENT,
                icon="mdi:fuse-blade",
                name="Heater power",
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=0,
                native_unit_of_measurement=UnitOfPower.WATT,
            ),
        ),
        # heater_power_rating
        SalerydLokeHeaterPowerRatingSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MODE_HEATER_POWER_RATING,
                icon="mdi:fuse-blade",
                name="Heater power rating",
                device_class=SensorDeviceClass.POWER,
                entity_category=EntityCategory.DIAGNOSTIC,
                suggested_display_precision=0,
                native_unit_of_measurement=UnitOfPower.WATT,
            ),
        ),
        # supply_fan_speed
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.FAN_SPEED_SUPPLY,
                icon="mdi:fan-speed-1",
                name="Supply fan speed",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        ),
        # extract_fan_speed
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.FAN_SPEED_EXHAUST,
                icon="mdi:fan-speed-2",
                name="Extract fan speed",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        ),
        # ventilation_mode
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MODE_FAN,
                name="Ventilation mode",
                icon="mdi:hvac",
                device_class=SensorDeviceClass.ENUM,
            ),
            options_enum=VentilationModeEnum,
        ),
        # target_temperature
        SalerydLokeTargetTemperatureSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MODE_TEMPERATURE,
                icon="mdi:home-thermometer",
                name="Target temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            ),
        ),
        # temperature_mode
        SalerydLokeEnumSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MODE_TEMPERATURE,
                icon="mdi:home-thermometer",
                name="Temperature mode",
                device_class=SensorDeviceClass.ENUM,
            ),
            options_enum=TemperatureModeEnum,
        ),
        # filter_months_left
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.FILTER_MONTHS_LEFT,
                icon="mdi:wrench-clock",
                name="Filter months left",
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MONTHS,
            ),
        ),
        # boost_mode_minutes_left
        SalerydLokeMinutesLeftSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MINUTES_LEFT_BOOST_MODE,
                icon="mdi:fan-clock",
                name="Boost mode minutes left",
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.MINUTES,
            ),
        ),
        # fireplace_mode_minutes_left
        SalerydLokeMinutesLeftSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MINUTES_LEFT_FIREPLACE_MODE,
                icon="mdi:fan-clock",
                name="Fireplace mode minutes left",
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.MINUTES,
            ),
        ),
        # control_system_name
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.MODEL_NAME,
                icon="mdi:barcode",
                name="System name",
                device_class=SensorDeviceClass.ENUM,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        # prod_nr
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.PRODUCT_NUMBER,
                icon="mdi:barcode",
                name="Product number",
                device_class=SensorDeviceClass.ENUM,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        # control_system_version
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.CONTROL_SYSTEM_VERSION,
                icon="mdi:wrench-clock",
                name="System version",
                device_class=SensorDeviceClass.ENUM,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        # normal mode target temperature
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.TARGET_TEMPERATURE_NORMAL,
                icon="mdi:home-thermometer",
                name="Normal temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        # Cool mode target temperature
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.TARGET_TEMPERATURE_COOL,
                icon="mdi:home-thermometer",
                name="Cool temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        # Economy mode target temperature
        SalerydLokeSensor(
            coordinator,
            entry,
            entity_description=SensorEntityDescription(
                key=DataKeyEnum.TARGET_TEMPERATURE_ECONOMY,
                icon="mdi:home-thermometer",
                name="Economy temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
    ]

    async_add_entities(sensors)
