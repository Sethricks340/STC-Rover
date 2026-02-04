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
        # |-> Test directions
# Make button or switch for reverse

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
    ws.connect("ws://stc_esp.local:81/ws")
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
        while True:
            if handeld is None:
                try:
                    handeld = serial.Serial("COM4", 115200, timeout=1)
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

        #layout
        layout = QVBoxLayout()

        self.handheld_status_label = QLabel("Handheld: Not Connected")
        layout.addWidget(self.handheld_status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_handheld_status(self, connected: bool):
        if connected:
            self.handheld_status_label.setText("Handheld: Connected")
        else:
            self.handheld_status_label.setText("Handheld: Disconnected")

    def send(self, motor, pot):
        # binary_msg = bytes([opcode, motor#, power, speed, direction])
        binary_msg = bytes([self.motor_opcode, motor, 1, pot, 0])
        ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
    
    def control_data(self, turn, pot, reverse): # TODO: reverse unused
        # print(f"Motor Joystick X={turn:.2f}, POT={pot}")
        turn_value = max(0, int(pot * (1 - min(1, abs(turn))))) # Clamp to never larger than 1, never below 0

        if (-0.1 <= turn <= 0.1):  # Deadspot = 0
            self.send(RIGHT_MOTORS, pot)  # we'll say motor 0 is RIGHT side, subject to future change
            self.send(LEFT_MOTORS, pot)
        elif (turn > 0.1): 
            self.send(LEFT_MOTORS, pot) # Send full to left motors
            self.send(RIGHT_MOTORS, turn_value) # Turning right, slow down right motors
        elif (turn < -0.1): 
            self.send(RIGHT_MOTORS, pot) # Send full to left motors
            self.send(LEFT_MOTORS, turn_value) # Turning left, slow down left motors
        else:
            self.send(RIGHT_MOTORS, pot) 
            self.send(LEFT_MOTORS, pot)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()