"""Binary sensor platform"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum
from pysaleryd.utils import ErrorSystemProperty, SystemProperty
from pysaleryd.websocket import State

from .const import KEY_CLIENT_STATE, ModeEnum
from .entity import SalerydLokeEntity

if TYPE_CHECKING:
    from .coordinator import SalerydLokeDataUpdateCoordinator
    from .data import SalerydLokeConfigEntry


class SalerydLokeBinarySensor(SalerydLokeEntity, BinarySensorEntity):
    """Sensor base class."""

    def __init__(
        self,
        coordinator: SalerydLokeDataUpdateCoordinator,
        entry: "SalerydLokeConfigEntry",
        entity_description: SensorEntityDescription,
        state_when_on: IntEnum = ModeEnum.On,
    ) -> None:
        """Initialize the sensor."""
        self.entity_id = (
            f"binary_sensor.{entry.unique_id}_{slugify(entity_description.name)}"
        )
        self.state_when_on = state_when_on
        super().__init__(coordinator, entry, entity_description)

    def _is_on(self, system_property: SystemProperty):
        return system_property.value

    @property
    def is_on(self):
        system_property = SystemProperty.from_str(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key),
        )
        if system_property.value is None:
            return

        return system_property.value == self.state_when_on.value

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


class SalerydLokeErrorMessageBinarySensor(SalerydLokeBinarySensor):

    @property
    def is_on(self):
        error = ErrorSystemProperty(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key, None),
        )
        if error.value is None:
            return

        return any(error.value)

    @property
    def extra_state_attributes(self):
        error = ErrorSystemProperty(
            self.entity_description.key,
            self.coordinator.data.get(self.entity_description.key, None),
        )
        if error.value is None:
            return None

        attrs = {}
        for v in error.value:
            attrs[v] = True

        return attrs


class SalerydLokeConnectionStateBinarySensor(SalerydLokeBinarySensor):

    def _get_extra_state_attributes(self, system_property: SystemProperty):
        if system_property.value is None:
            return None
        return {system_property.value: True}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: "SalerydLokeConfigEntry",
    async_add_entities: AddEntitiesCallback,
):
    """Setup binary sensor platform."""
    coordinator = entry.runtime_data.coordinator
    sensors = [
        # control_system_warning
        SalerydLokeErrorMessageBinarySensor(
            coordinator,
            entry,
            entity_description=BinarySensorEntityDescription(
                key=DataKeyEnum.ERROR_MESSAGE,
                icon="mdi:alert",
                name="System warning",
                device_class=BinarySensorDeviceClass.PROBLEM,
            ),
        ),
        # control_system_active
        SalerydLokeBinarySensor(
            coordinator,
            entry,
            entity_description=BinarySensorEntityDescription(
                key=DataKeyEnum.CONTROL_SYSTEM_STATE,
                icon="mdi:power",
                name="System active",
                device_class=BinarySensorDeviceClass.RUNNING,
            ),
        ),
        # heater_active
        SalerydLokeBinarySensor(
            coordinator,
            entry,
            entity_description=BinarySensorEntityDescription(
                key=DataKeyEnum.MODE_HEATER,
                icon="mdi:heating-coil",
                name="Heater active",
                device_class=BinarySensorDeviceClass.RUNNING,
            ),
        ),
        # connection_state
        SalerydLokeConnectionStateBinarySensor(
            coordinator,
            entry,
            entity_description=BinarySensorEntityDescription(
                key=KEY_CLIENT_STATE,
                icon="mdi:wrench-clock",
                name="Connection state",
                device_class=BinarySensorDeviceClass.CONNECTIVITY,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            state_when_on=State.RUNNING,
        ),
    ]

    async_add_entities(sensors)
