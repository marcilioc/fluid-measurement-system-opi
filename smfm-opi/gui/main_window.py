import json
from collections import deque
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Relative imports from other modules
from mqtt.mqtt_worker import MqttWorker
from utils.constants import (
    MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID, MQTT_KEEPALIVE_INTERVAL,
    TOPIC_WEIGHT_01, TOPIC_WEIGHT_02, TOPIC_STATUS_01, TOPIC_STATUS_02, TOPIC_LOG,
    COMMAND_TOPIC_01_PREFIX, COMMAND_TOPIC_02_PREFIX,
    MAX_PLOT_POINTS, PLOT_UPDATE_INTERVAL_MS
)

class ScaleMonitorWindow(QtWidgets.QMainWindow):
    """
    Main application window for monitoring and controlling load cells via MQTT.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Monitoramento de Fluidos por Massa")
        self.setGeometry(100, 100, 1000, 800) # x, y, width, height

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # List of topics that the MQTT worker should subscribe to
        self._mqtt_subscription_topics = [
            TOPIC_WEIGHT_01, TOPIC_WEIGHT_02, 
            TOPIC_STATUS_01, TOPIC_STATUS_02, 
            TOPIC_LOG
        ]
        # --- MQTT Thread Setup ---
        self.mqtt_thread = QtCore.QThread()
        self.mqtt_worker = MqttWorker(
            MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID, 
            MQTT_KEEPALIVE_INTERVAL, self._mqtt_subscription_topics
        )
        self.mqtt_worker.moveToThread(self.mqtt_thread)

        # Connect signals from worker to slots in main window
        self.mqtt_thread.started.connect(self.mqtt_worker.start_mqtt)
        self.mqtt_worker.message_received.connect(self.process_mqtt_message)
        self.mqtt_worker.connection_status.connect(self.update_mqtt_status)
        self.mqtt_worker.log_message.connect(self.log_message)
        
        # Start the MQTT thread
        self.mqtt_thread.start()

        # --- UI Elements ---
        self._create_mqtt_status_frame()
        self.scales_horizontal_layout = QtWidgets.QHBoxLayout()
        self._create_scale_frames() # Este método agora adicionará os frames ao layout horizontal
        self.main_layout.addLayout(self.scales_horizontal_layout) # Adicione o layout horizontal ao layout principal
        self._create_control_frame()
        self._create_log_frame()
        
        # Group of radio buttons for scale selection
        self.selected_scale_group = QtWidgets.QButtonGroup(self)
        self.radio_button_scale1 = QtWidgets.QRadioButton("Balança 01")
        self.radio_button_scale2 = QtWidgets.QRadioButton("Balança 02")
        self.selected_scale_group.addButton(self.radio_button_scale1, 1) # ID 1 for scale 01
        self.selected_scale_group.addButton(self.radio_button_scale2, 2) # ID 2 for scale 02
        self.radio_button_scale1.setChecked(True) # Default selection

        # Add radio buttons to the control frame layout
        control_layout = self.control_frame.layout()
        control_layout.addWidget(QtWidgets.QLabel("Selecionar Balança:"), 0, 0, 1, 3) # Spans 1 row, 3 columns
        control_layout.addWidget(self.radio_button_scale1, 0, 1)
        control_layout.addWidget(self.radio_button_scale2, 0, 2)

        # --- Plotting Data Initialization ---
        self.time_data_01 = deque(maxlen=MAX_PLOT_POINTS)
        self.weight_data_01 = deque(maxlen=MAX_PLOT_POINTS)
        self.time_data_02 = deque(maxlen=MAX_PLOT_POINTS)
        self.weight_data_02 = deque(maxlen=MAX_PLOT_POINTS)
        self.current_time_idx = 0 # Simple index for the X-axis of the plot (number of samples)

        # Configure plots within their respective frames
        self.plot_curve_01 = self.scale_frames["scale_01"]["plot_widget"].plot(pen=pg.mkPen(color='y', width=2)) # Yellow line
        self.plot_curve_02 = self.scale_frames["scale_02"]["plot_widget"].plot(pen=pg.mkPen(color='c', width=2)) # Cyan line

        # Timer for plot updates (separate from MQTT reception for performance)
        self.plot_timer = QtCore.QTimer(self)
        self.plot_timer.setInterval(PLOT_UPDATE_INTERVAL_MS) # Update plots every X ms
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start()

    def _create_mqtt_status_frame(self):
        self.mqtt_status_frame = QtWidgets.QGroupBox("Status MQTT")
        layout = QtWidgets.QVBoxLayout()
        self.mqtt_connection_label = QtWidgets.QLabel("MQTT: Desconectado")
        self.mqtt_connection_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.mqtt_connection_label, alignment=QtCore.Qt.AlignCenter)
        self.mqtt_status_frame.setLayout(layout)
        self.main_layout.addWidget(self.mqtt_status_frame)

    def _create_scale_frames(self):
        self.scale_frames = {}
        for i in range(1, 3): # For scale 01 and 02
            frame = QtWidgets.QGroupBox(f"Balança 0{i}")
            layout = QtWidgets.QGridLayout() # Using QGridLayout for better internal alignment

            # Weight and Status Labels
            weight_label_text = QtWidgets.QLabel("Peso Atual:")
            weight_value_label = QtWidgets.QLabel("0.000 kg")
            weight_value_label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
            
            status_label_text = QtWidgets.QLabel("Status:")
            status_value_label = QtWidgets.QLabel("Desconectado")

            layout.addWidget(weight_label_text, 0, 0)
            layout.addWidget(weight_value_label, 0, 1)
            layout.addWidget(status_label_text, 1, 0)
            layout.addWidget(status_value_label, 1, 1)

            # Plot Widget for this scale
            plot_widget = pg.PlotWidget()
            plot_widget.setTitle(f"Balança 0{i} - Peso em Tempo Real")
            plot_widget.setLabel('left', 'Peso', units='kg')
            plot_widget.setLabel('bottom', 'Tempo (amostras)')
            plot_widget.setBackground('k') # Black background
            plot_widget.showGrid(x=True, y=True) # Show grid

            layout.addWidget(plot_widget, 2, 0, 1, 2) # Row 2, Col 0, Spans 1 row, 2 columns

            frame.setLayout(layout)
            # NOVO: Adicione o frame ao layout horizontal das balanças
            self.scales_horizontal_layout.addWidget(frame) 
            self.scale_frames[f"scale_0{i}"] = {
                "weight_label": weight_value_label,
                "status_label": status_value_label,
                "plot_widget": plot_widget,
                "frame_layout": layout # Armazena o layout do frame para potencial adição futura
            }

    def _create_control_frame(self):
        self.control_frame = QtWidgets.QGroupBox("Controle e Calibração")
        layout = QtWidgets.QGridLayout() # Using QGridLayout for better alignment

        # Buttons and Inputs
        tare_button = QtWidgets.QPushButton("Tarar Balança")
        tare_button.clicked.connect(self.send_tare_command)
        layout.addWidget(tare_button, 1, 0, 1, 3) 

        auto_cal_zero_button = QtWidgets.QPushButton("Autocalibrar Zero")
        auto_cal_zero_button.clicked.connect(self.send_autocalibrate_zero_command)
        layout.addWidget(auto_cal_zero_button, 2, 0, 1, 3) 
        
        layout.addWidget(QtWidgets.QLabel("Peso Ref. (kg):"), 3, 0)
        self.ref_weight_entry = QtWidgets.QLineEdit()
        self.ref_weight_entry.setPlaceholderText("e.g., 100.0")
        layout.addWidget(self.ref_weight_entry, 3, 1)
        adjust_ref_button = QtWidgets.QPushButton("Ajustar com Referência")
        adjust_ref_button.clicked.connect(self.send_adjust_reference_command)
        layout.addWidget(adjust_ref_button, 3, 2)

        layout.addWidget(QtWidgets.QLabel("Fator Calib.:"), 4, 0)
        self.cal_factor_entry = QtWidgets.QLineEdit()
        self.cal_factor_entry.setPlaceholderText("e.g., 0.01")
        layout.addWidget(self.cal_factor_entry, 4, 1)
        set_cal_factor_button = QtWidgets.QPushButton("Definir Fator Calib.")
        set_cal_factor_button.clicked.connect(self.send_set_calibration_factor_command)
        layout.addWidget(set_cal_factor_button, 4, 2)

        self.control_frame.setLayout(layout)
        self.main_layout.addWidget(self.control_frame)

    def _create_log_frame(self):
        self.log_frame = QtWidgets.QGroupBox("Logs da Balança")
        layout = QtWidgets.QVBoxLayout()
        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.log_text_edit)
        self.log_frame.setLayout(layout)
        self.main_layout.addWidget(self.log_frame)

    @QtCore.pyqtSlot(str)
    def log_message(self, message):
        """Adds a message to the log area in the GUI. Called from MQTT worker thread via signal."""
        # This slot is executed in the GUI thread, so it's safe to update QTextEdit.
        self.log_text_edit.append(f"[{QtCore.QDateTime.currentDateTime().toString('HH:mm:ss')}] {message}")

    @QtCore.pyqtSlot(str)
    def update_mqtt_status(self, status_message):
        """Updates the MQTT connection status label. Called from MQTT worker thread via signal."""
        self.mqtt_connection_label.setText(f"MQTT: {status_message}")
        if status_message == "Conectado":
            self.mqtt_connection_label.setStyleSheet("color: green; font-weight: bold;")
        elif "Falha" in status_message or "Reconectando" in status_message:
            self.mqtt_connection_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.mqtt_connection_label.setStyleSheet("color: blue; font-weight: bold;")

    @QtCore.pyqtSlot(str, str)
    def process_mqtt_message(self, topic, payload):
        """Processes incoming MQTT messages and updates the GUI. Called from MQTT worker thread via signal."""
        try:
            # We increment the time index only when a weight message arrives for either scale
            # to keep the X-axis consistent across both plots if readings are roughly simultaneous.
            if topic in [TOPIC_WEIGHT_01, TOPIC_WEIGHT_02]:
                self.current_time_idx += 1 

            if topic == TOPIC_WEIGHT_01:
                weight = float(payload)
                self.scale_frames["scale_01"]["weight_label"].setText(f"{weight:.3f} kg")
                if len(self.weight_data_01) == MAX_PLOT_POINTS:
                    self.time_data_01.popleft()
                    self.weight_data_01.popleft()
                    self.time_data_01.append(self.current_time_idx)
                    self.weight_data_01.append(weight)
                else:
                    self.time_data_01.append(self.current_time_idx)
                    self.weight_data_01.append(weight)

            elif topic == TOPIC_WEIGHT_02:
                weight = float(payload)
                self.scale_frames["scale_02"]["weight_label"].setText(f"{weight:.3f} kg")
                self.time_data_02.append(self.current_time_idx)
                self.weight_data_02.append(weight)

            elif topic == TOPIC_STATUS_01:
                self.scale_frames["scale_01"]["status_label"].setText(payload)
            elif topic == TOPIC_STATUS_02:
                self.scale_frames["scale_02"]["status_label"].setText(payload)
            elif topic == TOPIC_LOG:
                self.log_message(f"LOG Balança: {payload}")
            else:
                self.log_message(f"Mensagem recebida: Tópico='{topic}', Payload='{payload}'")
        except ValueError:
            self.log_message(f"Error parsing payload from {topic}: '{payload}'")
        except Exception as e:
            self.log_message(f"Unknown error processing MQTT: {e}")

    @QtCore.pyqtSlot()
    def update_plots(self):
        """Updates the pyqtgraph plots with new data. Called by the QTimer."""
        # Set data for the plot curves.
        # list() is used to convert deque to list for pyqtgraph.
        self.plot_curve_01.setData(list(self.time_data_01), list(self.weight_data_01))
        self.plot_curve_02.setData(list(self.time_data_02), list(self.weight_data_02))

    def get_command_topic_prefix(self):
        """Returns the appropriate command topic prefix based on the selected scale."""
        selected_id = self.selected_scale_group.checkedId()
        if selected_id == 1: # Scale 01
            return COMMAND_TOPIC_01_PREFIX
        elif selected_id == 2: # Scale 02
            return COMMAND_TOPIC_02_PREFIX
        return "" # Should not happen

    def send_command(self, command_suffix, payload=""):
        """Generic method to send a command via MQTT."""
        topic_prefix = self.get_command_topic_prefix()
        if not topic_prefix: return

        command_topic = topic_prefix + command_suffix
        # Publish message through the worker thread
        self.mqtt_worker.publish_message(command_topic, payload)
        self.log_message(f"Command '{command_suffix}' sent to Scale {self.selected_scale_group.checkedId()}. Topic: {command_topic}, Payload: {payload if payload else 'N/A'}")

    # --- Command Sending Methods (slots connected to buttons) ---
    @QtCore.pyqtSlot()
    def send_tare_command(self):
        self.send_command("tare", "1")

    @QtCore.pyqtSlot()
    def send_autocalibrate_zero_command(self):
        self.send_command("autocalibrar_zero")

    @QtCore.pyqtSlot()
    def send_adjust_reference_command(self):
        try:
            ref_weight = float(self.ref_weight_entry.text())
            payload = json.dumps({"peso_referencia": ref_weight})
            self.send_command("ajustar_referencia", payload)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid number for the reference weight.")
        except Exception as e:
            self.log_message(f"Error preparing reference adjustment: {e}")

    @QtCore.pyqtSlot()
    def send_set_calibration_factor_command(self):
        try:
            cal_factor = float(self.cal_factor_entry.text())
            payload = json.dumps({"fator_calibracao": cal_factor})
            self.send_command("set_fator_calibracao", payload)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a valid number for the calibration factor.")
        except Exception as e:
            self.log_message(f"Error preparing calibration factor setting: {e}")

    def closeEvent(self, event):
        """Handles the window close event to gracefully stop the MQTT thread."""
        self.log_message("Closing application. Disconnecting MQTT...")
        self.mqtt_worker.stop_mqtt() # Tell the worker to stop MQTT
        self.mqtt_thread.quit()      # Tell the thread to quit its event loop
        self.mqtt_thread.wait()      # Wait for the thread to finish
        super().closeEvent(event)
