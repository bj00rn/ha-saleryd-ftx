"""Tests for estimated heater power and config flow step ids."""

from unittest.mock import MagicMock

from homeassistant import config_entries
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pysaleryd.const import DataKeyEnum
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.saleryd_hrv.const import DOMAIN
from custom_components.saleryd_hrv.sensor import SalerydLokeEstimatedHeaterPowerSensor


def _entry(unique_id="saleryd_ftx"):
    entry = MagicMock()
    entry.unique_id = unique_id
    entry.entry_id = "01TESTENTRY"
    entry.data = {}
    return entry


@pytest.mark.parametrize(
    ("rating_raw", "percent_raw", "expected"),
    [
        ("  0+  0+  1+0", "10", 90.0),  # Low rating, 900 W
        ("  1+  0+  1+0", "10", 180.0),  # High rating, 1800 W (raw values from LS-02)
        ("  1+  0+  1+0", "0", 0.0),
    ],
)
def test_estimated_heater_power(rating_raw, percent_raw, expected):
    """Estimated heater power is calculated for both low and high power rating."""
    coordinator = MagicMock()
    coordinator.data = {
        DataKeyEnum.MODE_HEATER_POWER_RATING: rating_raw,
        DataKeyEnum.HEATER_POWER_PERCENT: percent_raw,
    }
    sensor = SalerydLokeEstimatedHeaterPowerSensor(
        coordinator,
        _entry(),
        SensorEntityDescription(
            key=DataKeyEnum.HEATER_POWER_PERCENT, name="Heater power"
        ),
    )
    assert sensor.native_value == expected


async def test_user_flow_form_has_step_id(hass: HomeAssistant):
    """The user step form passes an explicit step_id."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_reconfigure_flow_form_has_step_id(hass: HomeAssistant):
    """The reconfigure step form passes an explicit step_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="Saleryd FTX",
        title="Saleryd FTX",
        data={
            "name": "Saleryd FTX",
            "websocket_ip": "192.168.1.151",
            "websocket_port": 3001,
            "enable_installer_settings": False,
            "installer_password": "",
        },
    )
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
