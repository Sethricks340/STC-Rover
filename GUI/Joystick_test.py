from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtCore import Qt, QPoint
import sys
import math

class Joystick(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.center = QPoint(100, 100)
        self.knob = QPoint(100, 100)
        self.radius = 80  # radius of joystick movement

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw base
        painter.setBrush(QBrush(QColor("lightgray")))
        painter.drawEllipse(self.center, self.radius, self.radius)
        # Draw knob
        painter.setBrush(QBrush(QColor("blue")))
        painter.drawEllipse(self.knob, 20, 20)

    def mousePressEvent(self, event):
        self.update_knob(event.position())

    def mouseMoveEvent(self, event):
        self.update_knob(event.position())

    def mouseReleaseEvent(self, event):
        self.knob = self.center
        self.update()
        print("X=0 Y=0")  # centered

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
        print(f"X={x_norm:.2f} Y={y_norm:.2f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Joystick()
    w.show()
    w1 = Joystick()
    w1.show()
    sys.exit(app.exec())
