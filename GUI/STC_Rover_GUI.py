# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life
# Known Issues:
# If ESP not connected, GUI crashes
# If try to connect GUI first, get this: Error receiving: [WinError 10054] An existing connection was forcibly closed by the remote host
# If doesn't actually connect (client rejected), still getting the GUI

import sys
import websocket

ws = websocket.WebSocket()
try:
    ws.connect("ws://stc_esp.local:81/ws")
    ws_connected = True
except Exception as e:
    print("WebSocket connection failed:", e)
    ws_connected = False
    sys.exit(1)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider
)

# Subclass QMainWindow
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STC Rover Control GUI")

        layout = QVBoxLayout()
        self.direction = 0 # Default forward
        self.motor_enabled = [False, False]
        self.motor_speed = [0,0]
        self.motor_opcode = 0000

        # First Vertical slider
        self.slider0 = QSlider(Qt.Orientation.Vertical)
        self.slider0.setMinimum(0)
        self.slider0.setMaximum(255)
        self.slider0.setValue(0)
        self.slider0.valueChanged.connect(lambda s: self.update_speed(0, s))

        # Second Vertical slider
        self.slider1 = QSlider(Qt.Orientation.Vertical)
        self.slider1.setMinimum(0)
        self.slider1.setMaximum(255)
        self.slider1.setValue(0)
        self.slider1.valueChanged.connect(lambda s: self.update_speed(1, s))

        self.motor0check = QCheckBox("MOTOR 0 ON")
        self.motor0check.setCheckState(Qt.CheckState.Unchecked)
        self.motor0check.stateChanged.connect(lambda s: self.motor_toggle(0, s))    
        
        self.motor1check = QCheckBox("MOTOR 1 ON")
        self.motor1check.setCheckState(Qt.CheckState.Unchecked)
        self.motor1check.stateChanged.connect(lambda s: self.motor_toggle(1, s))   

        self.reverse_button = QCheckBox("REVERSE")
        self.reverse_button.setCheckState(Qt.CheckState.Unchecked)
        self.reverse_button.stateChanged.connect(self.update_direction)

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.motor0check)
        layout.addWidget(self.motor1check)
        layout.addWidget(self.reverse_button)
        layout.addWidget(self.slider0)
        layout.addWidget(self.slider1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_speed(self, motor, value):
        self.motor_speed[motor] = value
        self.send_motor(motor)

    def motor_toggle(self, motor, state):
        self.motor_enabled[motor] = (state == Qt.CheckState.Checked.value)
        self.send_motor(motor)

    def update_direction(self, state):
        self.direction = 1 if state == Qt.CheckState.Checked.value else 0
        if self.motor_enabled[0]: self.send_motor(0)
        if self.motor_enabled[1]: self.send_motor(1)

    def send_motor(self, motor):
        if not self.motor_enabled[motor]:
            binary_msg = bytes([self.motor_opcode, motor, 0, self.motor_speed[motor], self.direction])
        else:
            binary_msg = bytes([self.motor_opcode, motor, 1, self.motor_speed[motor], self.direction])

        ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()