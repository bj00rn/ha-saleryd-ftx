"""Constants for saleryd_hrv."""

from enum import IntEnum
from logging import Logger, getLogger

# Base component constants
MANUFACTURER = "Saleryd"
DOMAIN = "saleryd_hrv"
DOMAIN_DATA = f"{DOMAIN}_data"
ATTRIBUTION = "Data provided by Saleryd HRV"
ISSUE_URL = "https://github.com/bj00rn/ha-saleryd-ftx/issues"
SUPPORTED_FIRMWARES = ["4.1.5"]
UNSUPPORTED_FIRMWARES = ["4.1.1"]
CONFIG_VERSION = 4

# Icons
ICON = "mdi:format-quote-close"

# Platforms
SENSOR = "sensor"
SWITCH = "switch"
CLIMATE = "climate"
SELECT = "select"
NUMBER = "number"
BUTTON = "button"
BINARY_SENSOR = "binary_sensor"
PLATFORMS = [SENSOR, SWITCH, SELECT, NUMBER, BUTTON, BINARY_SENSOR]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_WEBSOCKET_IP = "websocket_ip"
CONF_WEBSOCKET_PORT = "websocket_port"
CONF_INSTALLER_PASSWORD = "installer_password"
CONF_ENABLE_INSTALLER_SETTINGS = "enable_installer_settings"
CONF_VALUE = "value"

# Defaults
DEFAULT_NAME = DOMAIN

# Messages
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
%s %s
This is a custom integration!
If encounter any problems open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# Virtual keys, ie not present in data
KEY_CLIENT_STATE = "*HRV_CLIENT_STATE"
KEY_TARGET_TEMPERATURE = "*TARGET_TEMPERATURE"
KEY_COOKING_MODE = "*COOKING_MODE"


class TemperatureModeEnum(IntEnum):
    """Enum for temperature modes."""

    NORMAL = 0
    ECONOMY = 1
    COOL = 2


class VentilationModeEnum(IntEnum):
    """Enum for ventilation modes."""

    NORMAL = 0
    AWAY = 1
    BOOST = 2


class HeaterModeEnum(IntEnum):
    """Enum for heater modes."""

    LOW = 0
    HIGH = 1


class HeaterPowerEnum:
    """Enum for heater power ratings."""

    HIGH = 1800
    LOW = 900


class SystemActiveModeEnum(IntEnum):
    """Enum for system active modes."""

    OFF = 0
    ON = 1
    RESET = 2


class ModeEnum(IntEnum):
    """Enum for generic modes."""

    OFF = 0
    ON = 1


LOGGER: Logger = getLogger(__package__)

# Deprecated constants kept for migrations
DEPRECATED_CONF_MAINTENANCE_PASSWORD = "maintenance_password"
DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS = "enable_maintenance_settings"
