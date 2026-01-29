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
from PyQt6.QtWidgets import QApplication, QMainWindow, QCheckBox, QSlider, QHBoxLayout, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RC Car Controller")
        self.setWindowTitle("App Name")
        self.resize(600, 600)
        self.background_color = "#0F1C37"
        self.setStyleSheet(f"background-color: {self.background_color};")


        self.motor_on = False

        # Motor ON/OFF checkbox
        self.checkbox = QCheckBox("MOTOR ON")
        self.checkbox.setStyleSheet("color: white; font-size: 14px;")
        self.checkbox.stateChanged.connect(self.toggle_motor)

        # Vertical slider
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_speed)

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_motor(self, state):
        return
        # self.motor_on = state == Qt.CheckState.Checked.value
        # if self.motor_on:
        #     requests.get(f"http://192.168.0.50/on")
        # else:
        #     requests.get(f"http://192.168.0.50/off")
        #     self.slider.setValue(0)  # reset speed when motor is off

    def update_speed(self, value):
        return

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
