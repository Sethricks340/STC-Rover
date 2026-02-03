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
# Send Handheld joystick signals to motors
        # |-> Make directions correct

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

ws = websocket.WebSocket()
try:
    ws.connect("ws://stc_esp.local:81/ws")
    ws_connected = True
except Exception as e:
    print("WebSocket connection failed:", e)
    ws_connected = False
    # sys.exit(1) // TODO: Uncomment this

class SerialThread(QThread):
    data_received = pyqtSignal(float, float)

    def run(self):
        ser = serial.Serial("COM4", 115200, timeout=1)

        x = y = None
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line.startswith("X:"):
                x = float(line[2:])
            elif line.startswith("Y:"):
                y = float(line[2:])

            if x is not None and y is not None:
                self.data_received.emit(x, y)
                x = y = None

# Subclass QMainWindow
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STC Rover")

        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.motor_joystick_moved)
        self.serial_thread.start()

        layout = QVBoxLayout()
        self.motor_opcode = 0000

        # Layout
        layout = QHBoxLayout()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def motor_joystick_moved(self, x, y):
        print(f"Motor Joystick X={x:.2f}, Y={y:.2f}")

        # Note: (Wires to the RIGHT):
            # Middle: about -0.05 to 0.05
            # Up: Y to +1
            # Down: Y to -1
            # Right: X to -1
            # Left: X to +1

        # TODO: uncomment this to send message over WIFI
        # def send(motor, value):
        #     # speed = int(abs(value) * 255)
        #     # power = 0 if value == 0 else 1
        #     # direction = 1 if value < 0 else 0
        #     #     # binary_msg = bytes([opcode, motor#, power, speed, direction])
        #     # msg = bytes([self.motor_opcode, motor, power, speed if power else 0, direction if power else 0])
        #     # ws.send(msg, opcode=websocket.ABNF.OPCODE_BINARY)
        # send(0, x)
        # send(1, y)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()