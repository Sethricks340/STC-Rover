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
    QVBoxLayout
)

# Subclass QMainWindow to customize application's main window
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        # Central widget
        central = QWidget()
        layout = QVBoxLayout()

        motor0check = QCheckBox("MOTOR 0 ON")
        motor0check.setCheckState(Qt.CheckState.Unchecked)
        motor0check.stateChanged.connect(
            lambda s: self.motor_control(0, s)
        )
        
        motor1check = QCheckBox("MOTOR 1 ON")
        motor1check.setCheckState(Qt.CheckState.Unchecked)
        motor1check.stateChanged.connect(
            lambda s: self.motor_control(1, s)
        )

        layout.addWidget(motor0check)
        layout.addWidget(motor1check)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def motor_control(self, motor, state):
        if state == Qt.CheckState.Checked.value:
            requests.get(f"http://192.168.0.50/motor/{motor}/on")
        else:
            requests.get(f"http://192.168.0.50/motor/{motor}/off")
    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()