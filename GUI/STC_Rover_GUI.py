# TODO: Things the GUI might have:
    # Camera Feed
    # Camera Direction Gimball
    # 4-Directional Directional Control
    # Motor Speed control
    # Cellular connectivity status
    # GPS location
    # Battery life

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

        # Vertical slider
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_speed)

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
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_speed(self, value):
        print(f"Speed set to {value}")
        # Update motors that are currently ON
        if self.motor0check.isChecked():
            requests.get(f"http://192.168.0.50/motor/0/on/{value}")
        if self.motor1check.isChecked():
            requests.get(f"http://192.168.0.50/motor/1/on/{value}")


    def motor_control(self, motor, state):
        value = self.slider.value()
        if state == Qt.CheckState.Checked.value:
            requests.get(f"http://192.168.0.50/motor/{motor}/on/{value}")
        else:
            requests.get(f"http://192.168.0.50/motor/{motor}/off")
    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()