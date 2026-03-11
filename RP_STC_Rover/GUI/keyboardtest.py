# Source - https://stackoverflow.com/a/53210441
# Posted by Mitrek, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-10, License - CC BY-SA 4.0

from pynput.keyboard import Key, Listener

# CW, CCW, Forward, Backwards
direction = "off"
# 1, 2, 3
speed = 1
# clockwise, counter-clockwise
spin = "CW"

def on_press(key):
    global direction, spin, speed
    if (key == Key.up):
        direction = "forward"
        print(direction)
    elif (key == Key.down):
        direction = "backwards"
        print(direction)
    elif hasattr(key, 'char') and key.char == 'd':
        direction = spin
        print(direction)
    elif hasattr(key, 'char') and key.char == 's':
        spin = "CCW" if (spin == "CW") else "CCW"
    elif hasattr(key, 'char') and key.char == 'g':
        speed = 1 if (speed == 3) else speed + 1

def on_release(key):
    print('{0} release'.format(key))
    if key == Key.esc:
        # Stop listener
        return False

# Collect events until released
with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
