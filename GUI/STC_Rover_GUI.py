# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life
# If ESP not connected, GUI crashes

import sys
import requests

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

# Subclass QMainWindow to customize application's main window
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STC Rover Control GUI")

        layout = QVBoxLayout()

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

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.motor0check)
        layout.addWidget(self.motor1check)
        layout.addWidget(self.slider0)
        layout.addWidget(self.slider1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_speed0(self, value):
        print(f"Speed0 set to {value}")
        if self.motor0check.isChecked():
            requests.get(f"http://192.168.0.50/motor/0/on/{value}")

    def update_speed1(self, value):
        print(f"Speed1 set to {value}")
        if self.motor1check.isChecked():
            requests.get(f"http://192.168.0.50/motor/1/on/{value}")

    def motor_control(self, motor, state):
        # pick the correct slider
        slider = self.slider0 if motor == 0 else self.slider1
        value = slider.value()

        if state == Qt.CheckState.Checked.value:
            requests.get(f"http://192.168.0.50/motor/{motor}/on/{value}")
        else:
            requests.get(f"http://192.168.0.50/motor/{motor}/off")

    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()