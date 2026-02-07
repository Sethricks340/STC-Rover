# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life
# Known Issues:
# If doesn't actually connect (client rejected), still getting the GUI
# If lose connection with ESP, don't know. GUI keeps going with no alert
# Still doesn't connect from different WIFIs :(

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
try:
    ws.connect("ws://10.15.27.151:81/ws")
    print("WebSocket connection success!")
    ws_connected = True
except Exception as e:
    print("WebSocket connection failed:", e)
    ws_connected = False
    # sys.exit(1) 

class SerialThread(QThread):
    data_received = pyqtSignal(float, int, int)
    connection_changed = pyqtSignal(bool)

    def run(self):
        handeld = None
        x = pot = reverse = None
        while True:
            if handeld is None:
                try:
                    handeld = serial.Serial("COM5", 115200, timeout=1)
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
                    print(f"X: {x}, Pot: {pot}, Reverse: {reverse}")
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

        self.motor_opcode = 0  
        self.reverse = False # Initialize reverse bool to 0 (not reversed)
        self.ignore_reverse = False # For testing without handheld, ignore reverse input and just use pot for forward/backward

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

        self.handheld_status_label = QLabel("Handheld: Not Connected")
        self.handheld_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.handheld_status_label)

        self.car_connection_status_label = QLabel("Car Connected: Placeholder")
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

    def update_handheld_status(self, connected: bool):
        if connected:
            self.handheld_status_label.setText("Handheld: Connected")
        else:
            self.handheld_status_label.setText("Handheld: Disconnected")

    def send(self, motor, pot, reverse):
        # binary_msg = bytes([opcode, motor#, power, speed, direction])
        binary_msg = bytes([self.motor_opcode, motor, 1, pot, reverse])
        ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
    
    def control_data(self, turn, pot, reverse):
        turn_value = max(0, int(pot * (1 - min(1, abs(turn))))) # Clamp to never larger than 1, never below 0

        if (-0.1 <= turn <= 0.1):  # Deadspot = 0
            self.send(RIGHT_MOTORS, pot, reverse)  # we'll say motor 0 is RIGHT side, subject to future change
            self.send(LEFT_MOTORS, pot, reverse)
        elif (turn > 0.1): 
            self.send(LEFT_MOTORS, pot, reverse) # Send full to left motors
            self.send(RIGHT_MOTORS, turn_value, reverse) # Turning right, slow down right motors
        elif (turn < -0.1): 
            self.send(RIGHT_MOTORS, pot, reverse) # Send full to left motors
            self.send(LEFT_MOTORS, turn_value, reverse) # Turning left, slow down left motors
        else:
            self.send(RIGHT_MOTORS, pot, reverse) 
            self.send(LEFT_MOTORS, pot, reverse)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()