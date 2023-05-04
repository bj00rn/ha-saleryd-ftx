"""Constants for saleryd_hrv."""
# Base component constants
NAME = "Saleryd HRV integration"
MANUFACTURER = "Saleryd"
DOMAIN = "saleryd_hrv"
DOMAIN_DATA = f"{DOMAIN}_data"
ATTRIBUTION = "Data provided by Saleryd HRV"
ISSUE_URL = "https://github.com/bj00rn/ha-saleryd-ftx/issues"
SUPPORTED_FIRMWARES = ["4.1.1", "4.1.5"]
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
