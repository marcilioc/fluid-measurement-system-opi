import paho.mqtt.client as mqtt
from PyQt5 import QtCore

class MqttWorker(QtCore.QObject):
    """
    Worker object to handle MQTT client operations in a separate thread.
    Emits signals to communicate with the GUI thread.
    """
    # Signals to be emitted
    message_received = QtCore.pyqtSignal(str, str) # topic, payload
    connection_status = QtCore.pyqtSignal(str)     # status message
    log_message = QtCore.pyqtSignal(str)          # log message

    def __init__(self, broker, port, client_id, keepalive_interval, topics_to_subscribe=None):
        super().__init__()
        self._broker = broker
        self._port = port
        self._client_id = client_id
        self._keepalive = keepalive_interval
        self._topics_to_subscribe = topics_to_subscribe if topics_to_subscribe is not None else []
        self._client = None
        self._running = True

    def start_mqtt(self):
        """Initializes and connects the MQTT client."""
        self.log_message.emit(f"Attempting to connect to MQTT broker at {self._broker}:{self._port}...")
        
        # Initialize the MQTT client with Callback API Version 2
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self._client_id)
        
        # Connect callbacks for API V2
        self._client.on_connect = self._on_connect_v2
        self._client.on_message = self._on_message # on_message signature is compatible
        self._client.on_disconnect = self._on_disconnect_v2

        try:
            self._client.connect(self._broker, self._port, self._keepalive)
            # Start the MQTT network loop in a non-blocking way in this thread.
            # This is crucial so the GUI remains responsive.
            self._client.loop_start() 
            self.connection_status.emit("Conectado")
        except Exception as e:
            self.connection_status.emit("Erro de Conexão")
            self.log_message.emit(f"MQTT connection error: {e}")
            self.stop_mqtt() # Ensure cleanup if connection fails immediately

    def stop_mqtt(self):
        """Stops the MQTT client loop and disconnects gracefully."""
        self.log_message.emit("Stopping MQTT client...")
        self._running = False 
        if self._client:
            self._client.loop_stop() # Stop the internal thread if loop_start was used
            self._client.disconnect()
            self.log_message.emit("MQTT client disconnected.")
            self.connection_status.emit("Desconectado")

    # on_connect callback for API V2
    def _on_connect_v2(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code == 0:
            self.log_message.emit("Successfully connected to MQTT broker.")
            self.connection_status.emit("Conectado")
            # Subscribe to predefined topics after successful connection
            for topic in self._topics_to_subscribe:
                client.subscribe(topic)
                self.log_message.emit(f"Subscribed to topic: {topic}")
        else:
            self.log_message.emit(f"Failed to connect, return code {reason_code}")
            self.connection_status.emit(f"Falha na Conexão ({reason_code})")

    # on_message callback (signature compatible with V1 and V2)
    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        self.message_received.emit(msg.topic, payload)

    # on_disconnect callback for API V2
    def _on_disconnect_v2(self, client, userdata, reason_code, properties):
        self.log_message.emit(f"MQTT disconnected with result code {reason_code}. Reconnecting...")
        self.connection_status.emit("Reconectando...")
        # The paho-mqtt client's loop_start automatically tries to reconnect
        # for most disconnect reasons, so no explicit reconnect logic needed here.

    def publish_message(self, topic, payload):
        """Publishes a message to an MQTT topic."""
        if self._client and self._client.is_connected():
            try:
                self._client.publish(topic, payload)
                # self.log_message.emit(f"Published to {topic}: {payload}") # Optional: log all publications
            except Exception as e:
                self.log_message.emit(f"Error publishing to {topic}: {e}")
        else:
            self.log_message.emit(f"Cannot publish, MQTT client not connected.")
