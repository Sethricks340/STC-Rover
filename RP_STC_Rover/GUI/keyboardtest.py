# Source - https://stackoverflow.com/a/53210441
# Posted by Mitrek, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-10, License - CC BY-SA 4.0

from pynput.keyboard import Key, Listener

direction = "off"
speed = 1
spin = "CW"

def on_press(key):
    global direction, spin, speed

    if key == Key.up:
        direction = "forward"
        print(direction)

    elif key == Key.down:
        direction = "backwards"
        print(direction)

    elif hasattr(key, 'char') and key.char == 'd':
        direction = spin
        print(direction)

def on_release(key):
    global direction, spin, speed
    if key == Key.esc:
        return False
    
    elif hasattr(key, 'char') and key.char == 's':
        spin = "CCW" if spin == "CW" else "CW"
        print("spin:", spin)

    elif hasattr(key, 'char') and key.char == 'g':
        speed = 1 if speed == 3 else speed + 1
        print("speed:", speed)

    elif key in (Key.up, Key.down):
        direction = "off"
        print(direction)

    elif hasattr(key, 'char') and key.char == 'd':
        direction = "off"
        print(direction)

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()