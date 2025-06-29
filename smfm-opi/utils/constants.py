"""
Constants for the MQTT Scale Monitor application.
"""

# MQTT Broker Configuration
MQTT_BROKER = "localhost" # Change to your MQTT broker's IP address or hostname
MQTT_PORT = 1883
MQTT_CLIENT_ID = "python_pyqt_scale_monitor"
MQTT_KEEPALIVE_INTERVAL = 60 # Seconds

# MQTT Topics for Data Publication (ESP32 -> Python)
TOPIC_WEIGHT_01 = "medicao/balanca001/peso" # Changed to 001 for consistency if you add more
TOPIC_WEIGHT_02 = "medicao/balanca002/peso" # Changed to 002 for consistency
TOPIC_STATUS_01 = "balanca/status/001"
TOPIC_STATUS_02 = "balanca/status/002"
TOPIC_LOG = "balanca/log"

# MQTT Topics for Command Subscription (Python -> ESP32)
COMMAND_TOPIC_01_PREFIX = "comando/balanca001/"
COMMAND_TOPIC_02_PREFIX = "comando/balanca002/"

# Plotting Configuration
MAX_PLOT_POINTS = 300 # Maximum number of points to display on the graph
PLOT_UPDATE_INTERVAL_MS = 150 # Graph update interval in milliseconds
