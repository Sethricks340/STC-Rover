# TODO:
#   Closing out GUI (x on tab) causes stall. Ctrl+C works in terminal to close it. 
#   Crashes if server disconnects? (new issue)
#   Test on public / different wifi
#   Controls disconnect periodically??
#   Filter out low noise
#   Run car code on reboot

# Add speaker on car

# Elements to add / take away on the GUI
    # Spin direction
    # Gear

import sys
import os
import cv2  
import asyncio
import serial
import websockets
import websocket
import base64
import numpy as np
import sounddevice as sd
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QSlider
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QBrush, QColor

from pynput.keyboard import Key, Listener

direction = "off"
speed_index = 0
speeds = [235, 245, 255]
speed = 100
spin = "CW"

last_msg = None

start_time = time.time()

if os.name == 'nt':
    print("Windows OS")
elif os.name == 'posix':
    print("Linux or macOS")

RIGHT_MOTORS = 0
LEFT_MOTORS = 1

ws = websocket.WebSocket()

try:
    # Tailscale rover IP:
    ip_string = "ws://100.94.206.108:8081/motors"
    # 100.94.206.108 
    ws.connect(ip_string)
    print("Controls WebSocket connected")
    ws_connected = True
except Exception as e:
    print("Controls WebSocket connection failed:", e)
    ws_connected = False
    # sys.exit(1) 

ROBOT_TAILSCALE_IP = "100.94.206.108"  # Sender Pi IP
PORT = 8765

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1

speaker_index = sd.default.device[1]  # output device
# print(f"{speaker_index}")


class ReconnectThread(QThread):
    status_update = pyqtSignal(bool)

    def __init__(self, ip_string):
        super().__init__()
        self.ip_string = ip_string
        self.running = True

    def run(self):
        global ws, ws_connected
        while self.running and not ws_connected:
            self.status_update.emit(False)  # Update label immediately
            try:
                ws.close()
            except:
                pass
            try:
                ws = websocket.WebSocket()
                ws.connect(self.ip_string)
                ws_connected = True
                self.status_update.emit(True)  # Connection successful
            except Exception as e:
                print(f"Reconnect failed: {e}, retrying in 1 second...")
                time.sleep(1)


class SerialThread(QThread):
    # print(f"Opcode: {opcode}, Motor: {motor_number}, Power: {power}, PWM: {pwm}, Direction: {direction}")
    # self.data_received.emit(x, y, reverse, dime)
    data_received = pyqtSignal(float, float, int, int)
    connection_changed = pyqtSignal(bool)

    def run(self):

        def on_press(key):
            global direction, spin, speed, speed_index, last_msg

            msg = None
            if key == Key.up:
                direction = "forward"
                msg = (0, speed, 0, 0)
            elif key == Key.down:
                direction = "backwards"
                msg = (0, speed, 1, 0)
            elif hasattr(key, 'char') and key.char == 'd':
                direction = 1 if spin == "CCW" else -1
                msg = (0, speed, 0, direction)

            if msg != last_msg and msg is not None:
                self.data_received.emit(*msg)
                last_msg = msg

        def on_release(key):
            global direction, spin, speed, speed_index, last_msg
            
            if hasattr(key, 'char') and key.char == 's':
                spin = "CCW" if spin == "CW" else "CW"
                # print("spin:", spin)

            elif hasattr(key, 'char') and key.char == 'g':
                speed_index = 0 if speed_index == 2 else speed_index + 1
                speed = speeds[speed_index]
                # print("speed:", speed)

            elif key in (Key.up, Key.down) or (hasattr(key, 'char') and key.char == 'd'):
                direction = "off"
                # print(direction)
                msg = (0, 0, 0, 0)
                if msg != last_msg:
                    self.data_received.emit(*msg)
                    last_msg = msg

        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

# --- Thread to receive camera + audio ---
class CameraAudioThread(QThread):
    frame_received = pyqtSignal(np.ndarray)

    def run(self):
        asyncio.run(self.websocket_loop())

    async def websocket_loop(self):
        while True:
            try:
                uri = f"ws://{ROBOT_TAILSCALE_IP}:{PORT}"
                async with websockets.connect(uri) as websocket:
                    # Start audio stream
                    audio_stream = sd.OutputStream(device=speaker_index,
                                                   samplerate=AUDIO_RATE,
                                                   channels=AUDIO_CHANNELS)
                    audio_stream.start()

                    while True:
                        data = await websocket.recv()
                        if data.startswith("VID:"):
                            jpg_original = base64.b64decode(data[4:])
                            nparr = np.frombuffer(jpg_original, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            self.frame_received.emit(frame)
                        elif data.startswith("AUD:"):
                            audio_bytes = base64.b64decode(data[4:])
                            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)

                            gain = 3.0  
                            audio_array = np.clip(audio_array * gain, -1.0, 1.0)

                            audio_stream.write(audio_array)
            except (ConnectionRefusedError, OSError, websockets.exceptions.ConnectionClosed):
                await asyncio.sleep(2)

# --- GUI ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STC Rover")

        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.control_data)
        self.serial_thread.connection_changed.connect(self.update_handheld_status)
        self.serial_thread.start()
        self.reconnect_thread = None  # track if reconnection thread is active

        # Start reconnect thread if not connected
        if not ws_connected: self.start_reconnect()

        self.motor_opcode = 0  
        self.smoothed_y = 0  # keeps track of last smoothed Y value
        self.smoothed_turn = 0

        # Main layout
        layout = QHBoxLayout()
        infos_layout = QVBoxLayout()

        # Camera Feed
        self.camera_feed_label = QLabel("Camera Feed")
        self.camera_feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_feed_label.setMinimumSize(320, 240)
        self.camera_feed_label.setStyleSheet("""
            QLabel {
                border: 2px solid black;
                background-color: #000000;
                font-size: 20px;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.camera_feed_label, stretch=3)

        # self.handheld_status_label = QLabel("Handheld: Disconnected")
        # self.handheld_status_label.setStyleSheet("""
        #     QLabel {
        #         font-size: 20px;
        #     }
        # """)
        # infos_layout.addWidget(self.handheld_status_label)

        initial_connected_message = "Connected" if ws_connected else "Disconnected"
        self.controls_status_label = QLabel(f"Car Connected: {initial_connected_message}")
        self.controls_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.controls_status_label)
        
        self.spin_label = QLabel("Spin: Placeholder")
        self.spin_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.spin_label)

        self.gear_label = QLabel("Gear: Placeholder")
        self.gear_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.gear_label)

        layout.addLayout(infos_layout, stretch=1)

        # Container
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Start camera/audio thread
        self.cam_thread = CameraAudioThread()
        self.cam_thread.frame_received.connect(self.update_camera)
        self.cam_thread.start()

    def update_camera(self, frame):
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.camera_feed_label.setPixmap(pixmap.scaled(self.camera_feed_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def closeEvent(self, event):
        self.cam_thread.running = False
        self.cam_thread.quit()
        self.cam_thread.wait()
        event.accept()

    def start_reconnect(self):
        # Only start if no thread exists or the previous one stopped
        if self.reconnect_thread is None or not self.reconnect_thread.isRunning():
            self.reconnect_thread = ReconnectThread(ip_string)
            self.reconnect_thread.status_update.connect(self.update_car_status)
            self.reconnect_thread.start()

    def update_handheld_status(self, connected: bool):
        if connected:
            self.handheld_status_label.setText("Handheld: Connected")
        else:
            self.handheld_status_label.setText("Handheld: Disconnected")
            self.send(RIGHT_MOTORS, 0, 0)   # Turn off motors if handheld disconnected
            self.send(LEFT_MOTORS, 0, 0)    # Turn off motors if handheld disconnected

    def update_car_status(self, connected: bool):
        if connected:
            self.controls_status_label.setText("Car Connected: Connected")
        else:
            self.controls_status_label.setText("Car Connected: Disconnected")

    def send(self, motor, y, reverse):
        global ws_connected, ws
        binary_msg = bytes([self.motor_opcode, motor, 1, y, reverse])
        if not ws_connected:
            return

        try:
            ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
        # except (websocket.WebSocketConnectionClosedException, ConnectionResetError) as e:
        except Exception as e:
            print(f"WebSocket send failed: {e}")
            ws_connected = False
            self.start_reconnect()  # non-blocking reconnect

    def control_data(self, turn, y, reverse, dime):
        if not ws_connected:
            return  # skip everything if ESP is disconnected
        
        # dime is non-zero
        if (dime): 
            # print(f"dime1: {dime}")
            # print(f"dime1: {0 if dime>0 else 1}")
            # print(f"dime1: {0 if dime<0 else 1}")
            self.send(RIGHT_MOTORS, int(y), 0 if dime>0 else 1)
            self.send(LEFT_MOTORS, int(y), 0 if dime<0 else 1)
        else:
            self.send(RIGHT_MOTORS, int(y), reverse)
            self.send(LEFT_MOTORS, int(y), reverse)

app = QApplication(sys.argv)
window = MainWindow()
window.showFullScreen()
app.exec()
ws.close()