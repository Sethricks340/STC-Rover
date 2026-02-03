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
# Fix motor directions (joystick up = both forward -> right now joystick up = only pair 0 on)

import sys
import websocket
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
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

# Subclass QMainWindow
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STC Rover")

        layout = QVBoxLayout()
        self.motor_opcode = 0000

        # Layout
        layout = QHBoxLayout()

        # Motion Control Joystick
        joystick_container = QWidget()
        joystick_layout = QVBoxLayout()
        self.joystick = Joystick("blue", "lightgray")
        self.joystick.moved.connect(self.motor_joystick_moved)
        joystick_layout.addWidget(QLabel("Motion Control", alignment=Qt.AlignmentFlag.AlignCenter))
        joystick_layout.addWidget(self.joystick)
        joystick_container.setLayout(joystick_layout)
        layout.addWidget(joystick_container)

        # Camera Control Joystick
        joystick_container2 = QWidget()
        joystick_layout2 = QVBoxLayout()
        self.joystick2 = Joystick("lightgray", "blue")
        self.joystick2.moved.connect(self.camera_joystick_moved)
        joystick_layout2.addWidget(QLabel("Camera Control", alignment=Qt.AlignmentFlag.AlignCenter))
        joystick_layout2.addWidget(self.joystick2)
        joystick_container2.setLayout(joystick_layout2)
        layout.addWidget(joystick_container2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def motor_joystick_moved(self, x, y):
        print(f"Joystick 2 X={x:.2f}, Y={y:.2f}")
        def send(motor, value):
            speed = int(abs(value) * 255)
            power = 0 if value == 0 else 1
            direction = 1 if value < 0 else 0
                # binary_msg = bytes([opcode, motor#, power, speed, direction])
            msg = bytes([self.motor_opcode, motor, power, speed if power else 0, direction if power else 0])
            # ws.send(msg, opcode=websocket.ABNF.OPCODE_BINARY) // TODO: uncomment this
        send(0, x)
        send(1, y)

    def camera_joystick_moved(self, x, y):
        # For camera
        print(f"Joystick 2 X={x:.2f}, Y={y:.2f}")

class Joystick(QWidget):
    moved = pyqtSignal(float, float)
    def __init__(self, center_color="blue", outer_color="lightgray"):
        super().__init__()
        self.setFixedSize(200, 200)
        self.center = QPoint(100, 100)
        self.knob = QPoint(100, 100)
        self.radius = 80  # radius of joystick movement

        self.center_color = center_color
        self.outer_color = outer_color

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw base
        painter.setBrush(QBrush(QColor(self.outer_color)))
        painter.drawEllipse(self.center, self.radius, self.radius)
        # Draw knob
        painter.setBrush(QBrush(QColor(self.center_color)))
        painter.drawEllipse(self.knob, 20, 20)

    def mousePressEvent(self, event):
        self.update_knob(event.position())

    def mouseMoveEvent(self, event):
        self.update_knob(event.position())

    def mouseReleaseEvent(self, event):
        self.knob = self.center
        self.update()
        # print("X=0 Y=0")  # centered
        self.moved.emit(0, 0)

    def update_knob(self, pos):
        dx = pos.x() - self.center.x()
        dy = pos.y() - self.center.y()
        distance = math.hypot(dx, dy)
        if distance > self.radius:
            dx = dx * self.radius / distance
            dy = dy * self.radius / distance
        self.knob = QPoint(int(self.center.x() + dx), int(self.center.y() + dy))
        self.update()
        # Normalize output to -1 to 1
        x_norm = dx / self.radius
        y_norm = -dy / self.radius  # invert Y to match typical joystick convention
        # print(f"X={x_norm:.2f} Y={y_norm:.2f}")
        self.moved.emit(x_norm, y_norm)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()


from PyQt6.QtCore import QThread, pyqtSignal
import serial

class SerialThread(QThread):
    data_received = pyqtSignal(int, int)

    def run(self):
        ser = serial.Serial("COM4", 115200, timeout=1)

        x = y = None
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line.startswith("X:"):
                x = int(line[2:])
            elif line.startswith("Y:"):
                y = int(line[2:])

            if x is not None and y is not None:
                self.data_received.emit(x, y)
                x = y = None


