# ESP32-CAM Programming via Arduino Uno
This program uses the Arduino UNO as a USB-to_serial converter to program the ESP-32 cam. The ESP connects to the wifi and allows video streaming and viewing via the IP address.
## Wiring

| ESP32-CAM | Arduino Uno |
|-----------|-------------|
| U0R       | RX          |
| U0T       | TX          |
| 5V        | 5V          |
| GND       | GND         |
The UNO must also have the RST pin connected to the GND to bypass the UNO CPU. 
## Upload Procedure
1. Connect the ESP's IO0 to the ESP's GND. 
2. When the terminal prompts say "Connecting..." press the REST button on the ESP. 
3. Once the code is done uploading, disconnect the IO0 and GND and press the RST button again.
4. You should then be able to copy and paste the IP address from the serial moniter into your browser and see teh camera output.

## Troubleshooting
Possible Issue: '''A fatal error occurred: Failed to connect to ESP32: No serial data received.'''
Fix: Check wiring, make sure that the Arduino IDE is using the correct board/port. Unplug the UNO, reconnect, and try again.

Possible Issue: 
```
A fatal error occurred: The chip stopped responding. 
Connected to ESP32 on /dev/cu.usbmodem1101: 
Chip type: ESP32-D0WD-V3 (revision v3.1) 
Features: Wi-Fi, BT, Dual Core + LP Core, 240MHz, Vref calibration in eFuse, Coding Scheme None 
Crystal frequency: 40MHz 
MAC: d4:e9:f4:a1:fd:a4 
Uploading stub flasher... 
Running stub flasher... 
Stub flasher running. 
Changing baud rate to 460800... 
Changed. 
Hard resetting via RTS pin... 
Failed uploading: uploading error: exit status 2
```
Fix: Upload via terminal with this command
```
/Users/hjb/Library/Arduino15/packages/esp32/tools/esptool_py/5.1.0/esptool \
--chip esp32 \
--port "/dev/cu.usbmodem1101" \
--baud 115200 \
--before default-reset \
--after hard-reset \
write-flash -z \
--flash-mode keep \
--flash-freq keep \
--flash-size keep \
0x1000 "/Users/hjb/Library/Caches/arduino/sketches/8C766E4B3F952598527C25754B4F2B2C/CameraWebServer.ino.bootloader.bin" \
0x8000 "/Users/hjb/Library/Caches/arduino/sketches/8C766E4B3F952598527C25754B4F2B2C/CameraWebServer.ino.partitions.bin" \
0xe000 "/Users/hjb/Library/Arduino15/packages/esp32/hardware/esp32/3.3.7/tools/partitions/boot_app0.bin" \
0x10000 "/Users/hjb/Library/Caches/arduino/sketches/8C766E4B3F952598527C25754B4F2B2C/CameraWebServer.ino.bin"
```