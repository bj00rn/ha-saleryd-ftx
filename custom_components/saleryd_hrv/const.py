"""Constants for saleryd_hrv."""
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

# Other constants
CLIENT_STATE = "*HRV_CLIENT_STATE"

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
