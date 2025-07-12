"""
Constants for the MQTT Scale Monitor application.
"""

# MQTT Broker Configuration
MQTT_BROKER = "localhost" # Change to your MQTT broker's IP address or hostname
MQTT_PORT = 1883
MQTT_CLIENT_ID = "smfm_opi"
MQTT_KEEPALIVE_INTERVAL = 60 # Seconds

# MQTT Scales Topics Prefixes
SCALE_O1_PREFIX = "smfm/s01/"
SCALE_O2_PREFIX = "smfm/s02/"

# MQTT Topics for Data Publication (ESP32 -> Python)
TOPIC_WEIGHT_01 = SCALE_O1_PREFIX + "measurement/weight"
TOPIC_WEIGHT_02 = SCALE_O2_PREFIX + "measurement/weight"
TOPIC_STATUS_01 = SCALE_O1_PREFIX + "operation/status"
TOPIC_STATUS_02 = SCALE_O2_PREFIX + "operation/status"
TOPIC_LOG = "smfm/log"

# MQTT Topics for Command Subscription (Python -> ESP32)
START_COMMAND = "smfm/operation/start"
COMMAND_TOPIC_01_PREFIX = SCALE_O1_PREFIX + "operation/"
COMMAND_TOPIC_02_PREFIX = SCALE_O2_PREFIX + "operation/"

# Plotting Configuration
MAX_PLOT_POINTS = 300 # Maximum number of points to display on the graph
PLOT_UPDATE_INTERVAL_MS = 150 # Graph update interval in milliseconds
