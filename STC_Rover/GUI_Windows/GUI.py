# TODO:
#   Closing out GUI (x on tab) causes stall. Ctrl+C doesn't work either. Only the garbage terminal icon
#   Crashes if server disconnects? (new issue)
#   Filter out low noise from camera mic
#   Run car code on reboot
#   Double mic connection?
#   Better Camera Quality without huge delay?
#   Integrate camera controls?
#   Make chasis

import sys, os, cv2, asyncio, websockets, websocket, base64, time
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from pynput.keyboard import Key, Listener

direction = "off"
speed_index = 0
speeds = [235, 245, 255]
speed = 235
spin = "Counter-Clockwise"
last_msg = None
mic_enable = False

RIGHT_MOTORS = 0
LEFT_MOTORS = 1

AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
BLOCKSIZE = 2048 # For car speaker

ROBOT_TAILSCALE_IP = "100.94.206.108"  # Sender Pi IP
CAM_PORT = 8765
PI_SPEAK_PORT = 8766
MOTOR_PORT = 8081

motor_ws = websocket.WebSocket()
speaker_ws = websocket.WebSocket()

try:
    # Tailscale rover IP:
    motor_ip_string = f"ws://{ROBOT_TAILSCALE_IP}:{MOTOR_PORT}"
    motor_ws.connect(motor_ip_string, ping_interval=20, ping_timeout=5)
    print("Controls WebSocket connected")
    controls_connected = True
except Exception as e:
    print("Controls WebSocket connection failed:", e)
    controls_connected = False

try:
    # Tailscale rover IP:
    speak_ip_string = f"ws://{ROBOT_TAILSCALE_IP}:{PI_SPEAK_PORT}"
    speaker_ws.connect(speak_ip_string, ping_interval=20, ping_timeout=5)
    print("Speaker WebSocket connected")
    speaker_connected = True
except Exception as e:
    print("Speaker WebSocket connection failed:", e)
    speaker_connected = False

speaker_index = sd.default.device[1]  # audio output device

class ReconnectThread(QThread):
    controls_status_update = pyqtSignal(bool)
    speaker_status_update = pyqtSignal(bool)

    def __init__(self, ws_name: str, ip_string: str, check_interval: float = 1.0):
        super().__init__()
        self.ws_name = ws_name
        self.ip_string = ip_string
        self.check_interval = check_interval
        self.running = True

    def run(self):
        global motor_ws, speaker_ws, controls_connected, speaker_connected
        while self.running:
            ws_obj = globals()[self.ws_name]

            # Try sending a ping to detect connection alive
            is_connected = True
            try:
                ws_obj.send("PING", opcode=websocket.ABNF.OPCODE_TEXT)
            except:
                is_connected = False

            if not is_connected:
                if self.ws_name == "motor_ws":
                    controls_connected = False
                    self.controls_status_update.emit(False)
                else:
                    speaker_connected = False
                    self.speaker_status_update.emit(False)

                # Attempt reconnect
                while self.running and not is_connected:
                    try:
                        try:
                            ws_obj.close()
                        except:
                            pass
                        new_ws = websocket.WebSocket()
                        new_ws.connect(self.ip_string, ping_interval=20, ping_timeout=5)
                        globals()[self.ws_name] = new_ws
                        is_connected = True
                        if self.ws_name == "motor_ws":
                            controls_connected = True
                            self.controls_status_update.emit(True)
                        else:
                            speaker_connected = True
                            self.speaker_status_update.emit(True)
                        print(f"{self.ws_name} reconnected successfully!")
                    except Exception as e:
                        print(f"Reconnect failed for {self.ip_string}: {e}")
                        await_time = self.check_interval
                        # shorter sleep so it retries faster
                        time.sleep(await_time)
            else:
                time.sleep(self.check_interval)

class SerialThread(QThread):
    data_received = pyqtSignal(float, float, int, int)
    mic_change = pyqtSignal(bool)
    spin_gear_changed = pyqtSignal(str, int)

    def run(self):

        def on_press(key):
            global direction, spin, speed, speed_index, last_msg
            global mic_enable

            msg = None
            if key == Key.up:
                direction = "forward"
                msg = (0, speed, 0, 0)
            elif key == Key.down:
                direction = "backwards"
                msg = (0, speed, 1, 0)
            elif hasattr(key, 'char') and key.char == 'd':
                direction = 1 if spin == "Clockwise" else -1
                msg = (0, speed, 0, direction)
            elif key == Key.space and not mic_enable:
                mic_enable = True
                self.mic_change.emit(mic_enable)

            if msg != last_msg and msg is not None:
                self.data_received.emit(*msg)
                last_msg = msg

        def on_release(key):
            global direction, spin, speed, speed_index, last_msg
            global mic_enable
            
            if hasattr(key, 'char') and key.char == 's':
                spin = "Clockwise" if spin == "Counter-Clockwise" else "Counter-Clockwise"
                self.spin_gear_changed.emit(spin, speed_index)

            elif hasattr(key, 'char') and key.char == 'g':
                speed_index = 0 if speed_index == 2 else speed_index + 1
                speed = speeds[speed_index]
                self.spin_gear_changed.emit(spin, speed_index)

            elif key in (Key.up, Key.down) or (hasattr(key, 'char') and key.char == 'd'):
                direction = "off"
                msg = (0, 0, 0, 0)
                if msg != last_msg:
                    self.data_received.emit(*msg)
                    last_msg = msg

            elif key == Key.space and mic_enable:
                mic_enable = False
                self.mic_change.emit(mic_enable)

        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

# --- Thread to send audio data from mic ---
class MicStreamThread(QThread):
    def __init__(self, pi_ip, port, samplerate=48000, channels=1, blocksize=2048):
        super().__init__()
        self.pi_ip = pi_ip
        self.port = port
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.running = True
        self.mic_enable = False

    def enable_disable_mic(self, mic_enable):
        self.mic_enable = mic_enable
        print(f"self.mic_enable: {self.mic_enable}")

    def run(self):
        asyncio.run(self.websocket_loop())

    async def websocket_loop(self):
        audio_queue = asyncio.Queue()

        # Audio callback
        def audio_callback(indata, frames, time, status):
            audio_queue.put_nowait(indata.copy().tobytes())

        stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            blocksize=self.blocksize,
            dtype='float32',
            callback=audio_callback
        )
        stream.start()

        while self.running:
            try:
                async with websockets.connect(f"ws://{self.pi_ip}:{self.port}") as ws:
                    print(f"Connected to Pi mic at ws://{self.pi_ip}:{self.port}")
                    while self.running:
                        if not audio_queue.empty():
                            audio_bytes = await audio_queue.get()
                            audio_text = base64.b64encode(audio_bytes).decode('utf-8')
                            await ws.send(f"MIC:{audio_text}")
                        else:
                            await asyncio.sleep(0.005)
            except (ConnectionRefusedError, OSError, websockets.exceptions.ConnectionClosed):
                print(f"Speaker reconnect failed, retrying in 2s...")
                await asyncio.sleep(2)

# --- Thread to receive camera + audio ---
class CameraAudioThread(QThread):
    frame_received = pyqtSignal(np.ndarray)

    def run(self):
        asyncio.run(self.websocket_loop())

    async def websocket_loop(self):
        while True:
            try:
                uri = f"ws://{ROBOT_TAILSCALE_IP}:{CAM_PORT}"
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
                print(f"Camera/Mic reconnect failed, retrying in 2s...")
                await asyncio.sleep(2)

# --- GUI ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STC Rover")
        global spin, speed
        self.motor_opcode = 0  

        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.control_data)
        self.serial_thread.start()
        self.controls_reconnect_thread = None  # track if controls reconnection thread is active
        self.cam_reconnect_thread = None  # track if controls reconnection thread is active
        self.serial_thread.spin_gear_changed.connect(self.update_spin_gear)

        self.mic_thread = MicStreamThread(ROBOT_TAILSCALE_IP, PI_SPEAK_PORT, blocksize=BLOCKSIZE)
        self.mic_thread.start()
        self.serial_thread.mic_change.connect(self.mic_thread.enable_disable_mic) # TODO: connect this to a function to disable the speaker
        self.serial_thread.mic_change.connect(self.update_mic_label)

        # Start reconnect thread if not connected
        if not controls_connected: self.start_reconnect()

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

        initial_speak_connected_message = "Connected" if speaker_connected else "Disconnected"
        self.speaker_connected_label = QLabel(f"Speaker: {initial_speak_connected_message}")
        self.speaker_connected_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.speaker_connected_label)

        initial_controls_connected_message = "Connected" if controls_connected else "Disconnected"
        self.controls_status_label = QLabel(f"Controls: {initial_controls_connected_message}")
        self.controls_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.controls_status_label)

        self.mic_status_label = QLabel("Mic: Disabled")
        self.mic_status_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.mic_status_label)
        
        self.spin_label = QLabel(f"Spin: {spin}")
        self.spin_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
            }
        """)
        infos_layout.addWidget(self.spin_label)

        self.gear_label = QLabel(f"Gear: {speed_index + 1}")
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

    def update_mic_label(self, mic_enabled):
        if mic_enabled:
            self.mic_status_label.setText("Mic: Enabled")
        else:
            self.mic_status_label.setText("Mic: Disabled")

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

        self.mic_thread.running = False
        self.mic_thread.quit()
        self.mic_thread.wait()
        event.accept()

    def start_reconnect(self):
        # Only start if no thread exists or the previous one stopped
        if self.controls_reconnect_thread is None or not self.controls_reconnect_thread.isRunning():
            # Motor reconnect
            self.controls_reconnect_thread = ReconnectThread("motor_ws", motor_ip_string, 1.0)
            self.controls_reconnect_thread.start()
            self.controls_reconnect_thread.controls_status_update.connect(self.update_controls_status)

        if self.cam_reconnect_thread is None or not self.cam_reconnect_thread.isRunning():
            # Speaker reconnect
            self.cam_reconnect_thread = ReconnectThread("speaker_ws", speak_ip_string, 1.0)
            self.cam_reconnect_thread.start()
            self.cam_reconnect_thread.speaker_status_update.connect(self.update_speaker_status) 

    def update_spin_gear(self, spin_val, gear_index):
        self.spin_label.setText(f"Spin: {spin_val}")
        self.gear_label.setText(f"Gear: {gear_index + 1}")

    def update_controls_status(self, connected: bool):
        if connected:
            self.controls_status_label.setText("Controls: Connected")
        else:
            self.controls_status_label.setText("Controls: Disconnected")
    def update_speaker_status(self, connected: bool):
        if connected:
            self.speaker_connected_label.setText("Speaker: Connected")
        else:
            self.speaker_connected_label.setText("Speaker: Disconnected")

    def send(self, motor, y, reverse):
        global controls_connected, motor_ws
        binary_msg = bytes([self.motor_opcode, motor, 1, y, reverse])
        if not controls_connected:
            return

        try:
            motor_ws.send(binary_msg, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print(f"WebSocket send failed: {e}")
            controls_connected = False
            self.start_reconnect()  # non-blocking reconnect

    def control_data(self, turn, y, reverse, dime):
        if not controls_connected:
            return  # skip everything if ESP is disconnected
        
        # dime is non-zero
        if (dime): 
            self.send(RIGHT_MOTORS, int(y), 0 if dime>0 else 1)
            self.send(LEFT_MOTORS, int(y), 0 if dime<0 else 1)
        else:
            self.send(RIGHT_MOTORS, int(y), reverse)
            self.send(LEFT_MOTORS, int(y), reverse)

app = QApplication(sys.argv)
window = MainWindow()
window.showFullScreen()
app.exec()
motor_ws.close()