# TODO: Things the GUI might have:
    # Camera
    # 4-Directional Motor Control
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
)

# Subclass QMainWindow to customize application's main window
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        widget = QCheckBox("LED2 ON")
        widget.setCheckState(Qt.CheckState.Checked)

        widget.stateChanged.connect(self.show_state)

        self.setCentralWidget(widget)

    def show_state(self, s):
        if s == Qt.CheckState.Checked.value:
            requests.get("http://192.168.0.50/on")
        else:
            requests.get("http://192.168.0.50/off")
    
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()