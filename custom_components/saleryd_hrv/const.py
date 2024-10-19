"""Constants for saleryd_hrv."""

from logging import Logger, getLogger

# Base component constants
NAME = "Saleryd HRV integration"
MANUFACTURER = "Saleryd"
DOMAIN = "saleryd_hrv"
DOMAIN_DATA = f"{DOMAIN}_data"
ATTRIBUTION = "Data provided by Saleryd HRV"
ISSUE_URL = "https://github.com/bj00rn/ha-saleryd-ftx/issues"
SUPPORTED_FIRMWARES = ["4.1.5"]
UNSUPPORTED_FIRMWARES = ["4.1.1"]
# Icons
ICON = "mdi:format-quote-close"

# Platforms
SENSOR = "sensor"
SWITCH = "switch"
CLIMATE = "climate"
PLATFORMS = [SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_WEBSOCKET_IP = "websocket_ip"
CONF_WEBSOCKET_PORT = "websocket_port"

# Defaults
DEFAULT_NAME = DOMAIN

# Messages
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME} %s
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# Virtual keys, ie not present in data
KEY_CLIENT_STATE = "*HRV_CLIENT_STATE"
KEY_TARGET_TEMPERATURE = "*TARGET_TEMPERATURE"
KEY_COOKING_MODE = "*COOKING_MODE"

TEMPERATURE_MODE_NORMAL = 0
TEMPERATURE_MODE_ECO = 1
TEMPERATURE_MODE_COOL = 2

VENTILATION_MODE_HOME = 0
VENTILATION_MODE_AWAY = 1
VENTILATION_MODE_BOOST = 2

HEATER_MODE_LOW = 0
HEATER_MODE_HIGH = 1

SYSTEM_ACTIVE_MODE_ON = 1
SYSTEM_ACTIVE_MODE_OFF = 0
SYSTEM_ACTIVE_MODE_RESET = 2

MODE_ON = 1
MODE_OFF = 0

# Services
SERVICE_SET_FIREPLACE_MODE = "set_fireplace_mode"
SERVICE_SET_COOLING_MODE = "set_cooling_mode"
SERVICE_SET_VENTILATION_MODE = "set_ventilation_mode"
SERVICE_SET_TEMPERATURE_MODE = "set_temperature_mode"
SERVICE_UNLOCK_MAINTENANCE_SETTINGS = "unlock_maintenance_settings"
SERVICE_SET_SYSTEM_ACTIVE_MODE = "set_system_active_mode"

LOGGER: Logger = getLogger(__package__)
