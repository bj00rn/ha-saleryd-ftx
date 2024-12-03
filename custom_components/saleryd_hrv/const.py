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
PLATFORMS = [SENSOR, SWITCH, SELECT, NUMBER, BUTTON]


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
    Normal = 0
    Economy = 1
    Cool = 2


class VentilationModeEnum(IntEnum):
    Normal = 0
    Away = 1
    Boost = 2


class HeaterModeEnum(IntEnum):
    Low = 0
    High = 1


class HeaterPowerEnum:
    High = 1800
    Low = 900


class SystemActiveModeEnum(IntEnum):
    Off = 0
    On = 1
    Reset = 2


class ModeEnum(IntEnum):
    Off = 0
    On = 1


LOGGER: Logger = getLogger(__package__)

# Deprecated constants kept for migrations
DEPRECATED_CONF_MAINTENANCE_PASSWORD = "maintenance_password"
DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS = "enable_maintenance_settings"
