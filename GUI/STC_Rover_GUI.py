# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life
# If ESP not connected, GUI crashes
# If try to connect GUI first, get this: Error receiving: [WinError 10054] An existing connection was forcibly closed by the remote host
# Add directional Control (backwards/ forwards)
# Directional control updates motors without changing slider

import sys
import websocket

ws = websocket.WebSocket()
ws.connect("ws://192.168.0.50/ws")

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

        # First Vertical slider
        self.slider0 = QSlider(Qt.Orientation.Vertical)
        self.slider0.setMinimum(0)
        self.slider0.setMaximum(255)
        self.slider0.setValue(0)
        self.slider0.valueChanged.connect(self.update_speed0)

        # Second Vertical slider
        self.slider1 = QSlider(Qt.Orientation.Vertical)
        self.slider1.setMinimum(0)
        self.slider1.setMaximum(255)
        self.slider1.setValue(0)
        self.slider1.valueChanged.connect(self.update_speed1)

        self.motor0check = QCheckBox("MOTOR 0 ON")
        self.motor0check.setCheckState(Qt.CheckState.Unchecked)
        self.motor0check.stateChanged.connect(
            lambda s: self.motor_control(0, s)
        )
        
        self.motor1check = QCheckBox("MOTOR 1 ON")
        self.motor1check.setCheckState(Qt.CheckState.Unchecked)
        self.motor1check.stateChanged.connect(
            lambda s: self.motor_control(1, s)
        )

        self.reverse_button = QCheckBox("REVERSE")
        self.reverse_button.setCheckState(Qt.CheckState.Unchecked)
        self.reverse_button.stateChanged.connect(
            self.update_direction
        )

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

    def update_direction(self, state):
        if state == Qt.CheckState.Checked.value:
            self.direction = 1 # Reverse
            print(f"self.direction: {self.direction}")
        else:
            self.direction = 0 # Forward
            print(f"self.direction: {self.direction}")

    def update_speed0(self, value):
        print(f"Speed0 set to {value}")
        if self.motor0check.isChecked():
            ws.send(f"/motor/0/on/{value}/{self.direction}")

    def update_speed1(self, value):
        print(f"Speed1 set to {value}")
        if self.motor1check.isChecked():
            ws.send(f"/motor/1/on/{value}/{self.direction}")

    def motor_control(self, motor, state):
        # pick the correct slider
        slider = self.slider0 if motor == 0 else self.slider1
        value = slider.value()

        if state == Qt.CheckState.Checked.value:
            ws.send(f"/motor/{motor}/on/{value}/{self.direction}")
        else:
            ws.send(f"/motor/{motor}/off")

    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
ws.close()