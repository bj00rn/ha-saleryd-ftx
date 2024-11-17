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
PLATFORMS = [SENSOR, SWITCH, SELECT]


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
If you have any issues with this you need to open an issue here:
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
    Home = 0
    Away = 1
    Boost = 2


class HeaterModeEnum(IntEnum):
    Low = 0
    High = 1


class SystemActiveModeEnum(IntEnum):
    Off = 0
    On = 1
    Reset = 2


class ModeEnum(IntEnum):
    On = 1
    Off = 0


# Services
SERVICE_SET_FIREPLACE_MODE = "set_fireplace_mode"
SERVICE_SET_COOLING_MODE = "set_cooling_mode"
SERVICE_SET_VENTILATION_MODE = "set_ventilation_mode"
SERVICE_SET_TEMPERATURE_MODE = "set_temperature_mode"
SERVICE_SET_SYSTEM_ACTIVE_MODE = "set_system_active_mode"
SERVICE_SET_TARGET_TEMPERATURE_COOL = "set_target_temperature_cool"
SERVICE_SET_TARGET_TEMPERATURE_NORMAL = "set_target_temperature_normal"
SERVICE_SET_TARGET_TEMPERATURE_ECONOMY = "set_target_temperature_economy"

LOGGER: Logger = getLogger(__package__)

# Deprecated constants kept for migrations
DEPRECATED_CONF_MAINTENANCE_PASSWORD = "maintenance_password"
DEPRECATED_CONF_ENABLE_MAINTENANCE_SETTINGS = "enable_maintenance_settings"
