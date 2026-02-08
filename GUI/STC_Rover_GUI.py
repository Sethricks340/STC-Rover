# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life
# Known Issues:
# GUI doesn't crash when ESP disconnects, but it is slow to realize it (to changing the connected label)

import time
import serial
import sys
import websocket
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QThread
import math
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLabel
)

RIGHT_MOTORS = 0
LEFT_MOTORS = 1

ws = websocket.WebSocket()
ws.settimeout(1)  

try:
    ip_string = "ws://stc_esp.local:81/ws"
    # ip_string = "ws://10.15.27.151:81/ws"
    ws.connect(ip_string)
    print("WebSocket connection success!")
    ws_connected = True
except Exception as e:
    print("WebSocket connection failed:", e)
    ws_connected = False
    # sys.exit(1) 

class ReconnectThread(QThread):
    status_update = pyqtSignal(bool)

    def __init__(self, ip_string):
        super().__init__()
        self.ip_string = ip_string
        self.running = True

    def run(self):
        global ws, ws_connected
        while self.running and not ws_connected:
            self.status_update.emit(False)  # Update label immediately
            try:
                ws.close()
            except:
                pass
            try:
                ws = websocket.WebSocket()
                ws.connect(self.ip_string)
                ws_connected = True
                self.status_update.emit(True)  # Connection successful
            except Exception as e:
                print(f"Reconnect failed: {e}, retrying in 1 second...")
                time.sleep(1)

class SerialThread(QThread):
    data_received = pyqtSignal(float, int, int)
    connection_changed = pyqtSignal(bool)

    def run(self):
        handeld = None
        x = pot = reverse = None
        while True:
            if handeld is None:
                try:
                    handeld = serial.Serial("COM4", 115200, timeout=1) # TODO: Search for COM instead of hardcoding 
                    print("Handheld connected")
                    self.connection_changed.emit(True)
                except serial.SerialException:
                    print("Handheld not connected, retrying in 1 second...")
                    self.connection_changed.emit(False)
                    self.msleep(1000)
                    continue  # try again

            try:
                line = handeld.readline().decode(errors="ignore").strip()
                if line.startswith("X:"):
                    x = float(line[2:])
                elif line.startswith("P:"):
                    pot = int(line[2:])
                elif line.startswith("R:"):
                    reverse = int(line[2:])

                if x is not None and pot is not None and reverse is not None:
                    self.data_received.emit(x, pot, reverse)
                    # print(f"X: {x}, Pot: {pot}, Reverse: {reverse}")
                    x = pot = reverse = None

            except (serial.SerialException, OSError) as e:
                print(f"Handheld disconnected: {e}")
                try:
                    handeld.close()
                except:
                    pass    
                self.data_received.emit(0, 0, 0) # Turn off motors
                self.connection_changed.emit(False)
                handeld = None  # will retry connection on next loop
            except ValueError:
                continue  # ignore bad lines

# Subclass QMainWindow
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STC Rover")

        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.control_data)
        self.serial_thread.connection_changed.connect(self.update_handheld_status)
        self.serial_thread.start()
        self.reconnect_thread = None  # track if reconnection thread is active

        # Start reconnect thread if not connected
        if not ws_connected: self.start_reconnect()

        self.motor_opcode = 0  
        self.direction = 0 # Initialize reverse bool to 0 (not reversed)
        self.ignore_serial = False # For testing without handheld, ignore reverse input and just use pot for forward/backward

        #layout
        layout = QHBoxLayout()

        infos_layout = QVBoxLayout()

        self.camera_feed_label = QLabel("Camera Feed Placeholder")
        self.camera_feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_feed_label.setMinimumSize(320, 240)
        self.camera_feed_label.setStyleSheet("""
            QLabel {
                border: 2px solid black;
                background-color: #000000;
                font-size: 20px;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.camera_feed_label, stretch=3)

        self.handheld_status_label = QLabel("Handheld: Disconnected")
        self.handheld_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.handheld_status_label)

        initial_connected_message = "Connected" if ws_connected else "Disconnected"
        self.car_connection_status_label = QLabel(f"Car Connected: {initial_connected_message}")
        self.car_connection_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.car_connection_status_label)
        
        self.GPS_location_label = QLabel("GPS: Placeholder")
        self.GPS_location_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.GPS_location_label)

        self.battery_location_label = QLabel("Battery: Placeholder")
        self.battery_location_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.battery_location_label)

        layout.addLayout(infos_layout, stretch=1)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_reconnect(self):
        # Only start if no thread exists or the previous one stopped
        if self.reconnect_thread is None or not self.reconnect_thread.isRunning():
            self.reconnect_thread = ReconnectThread(ip_string)
            self.reconnect_thread.status_update.connect(self.update_car_status)
            self.reconnect_thread.start()

    def update_handheld_status(self, connected: bool):
        if connected:
            self.handheld_status_label.setText("Handheld: Connected")
        else:
            self.handheld_status_label.setText("Handheld: Disconnected")

    def update_car_status(self, connected: bool):
        if connected:
            self.car_connection_status_label.setText("Car Connected: Connected")
        else:
            self.car_connection_status_label.setText("Car Connected: Disconnected")

    # def send(self, motor, pot, reverse):
    #     # binary_msg = bytes([opcode, motor#, power, speed, direction])
    #     binary_msg = bytes([self.motor_opcode, motor, 1, pot, reverse])
    #     ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)

    def send(self, motor, pot, reverse):
        global ws_connected, ws
        binary_msg = bytes([self.motor_opcode, motor, 1, pot, reverse])
        if not ws_connected:
            return

        try:
            ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
        except (websocket.WebSocketConnectionClosedException, ConnectionResetError) as e:
            print(f"WebSocket send failed: {e}")
            ws_connected = False
            self.start_reconnect()  # non-blocking reconnect
        def reconnect_ws(self):
            global ws_connected, ws
            ws_connected = False
            self.update_car_status(False)
            while not ws_connected:
                try:
                    ws.close()  # just in case
                except:
                    pass
                try:
                    ws = websocket.WebSocket()
                    ws.connect(ip_string)
                    ws_connected = True
                    print("Reconnected to WebSocket!")
                except Exception as e:
                    print(f"Reconnect failed: {e}, retrying in 1 second...")
                    time.sleep(1)

    def control_data(self, turn, pot, reverse):
        if not ws_connected:
            return  # skip everything if ESP is disconnected
        if self.ignore_serial:
            return  # skip new direction flips while handling current one

        # print(f"Control data received")

        # Only allow one flip at a time
        if self.direction != reverse:
            self.ignore_serial = True
            print(f"changed direction from {self.direction} to {reverse} at speed {pot}")

            current_pot = pot
            # ramp down
            for speed in range(current_pot, 29, -5):
                self.send(LEFT_MOTORS, speed, self.direction)
                self.send(RIGHT_MOTORS, speed, self.direction)
                time.sleep(0.05)

            self.direction = reverse
            # ramp up
            for speed in range(30, current_pot + 1, 5):
                self.send(LEFT_MOTORS, speed, self.direction)
                self.send(RIGHT_MOTORS, speed, self.direction)
                time.sleep(0.05)

            self.ignore_serial = False

        # normal turning
        turn_value = max(0, int(pot * (1 - min(1, abs(turn)))))

        try:
            if -0.1 <= turn <= 0.1:
                self.send(RIGHT_MOTORS, pot, reverse)
                self.send(LEFT_MOTORS, pot, reverse)
            elif turn > 0.1:
                self.send(LEFT_MOTORS, pot, reverse)
                self.send(RIGHT_MOTORS, turn_value, reverse)
            elif turn < -0.1:
                self.send(RIGHT_MOTORS, pot, reverse)
                self.send(LEFT_MOTORS, turn_value, reverse)
        except (websocket.WebSocketConnectionClosedException, ConnectionResetError):
            print("ESP disconnected during normal send, skipping frame")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()