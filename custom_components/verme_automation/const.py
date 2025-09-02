"""Constants for the Verme Automation integration."""

from .version import __version__

DOMAIN = "verme_automation"

# Integration version
VERSION = __version__

# Configuration keys
CONF_MQTT_HOST = "mqtt_host"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"

# Default values
DEFAULT_MQTT_PORT = 1883

# MQTT Topics
MQTT_BASE_TOPIC = "verme"
MQTT_SHADES_TOPIC = f"{MQTT_BASE_TOPIC}/shades"
MQTT_NODE_SUFFIX = "node"
MQTT_POSITION_SUFFIX = "position"
MQTT_STATE_SUFFIX = "state"
MQTT_STATUS_SUFFIX = "status"

# Node types
NODE_TYPE_SHADE = "shade"

# Device info
MANUFACTURER = "Verme"
MODEL_SHADE = "Verme Shade"
