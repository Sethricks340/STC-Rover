# Source - https://stackoverflow.com/a/53210441
# Posted by Mitrek, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-10, License - CC BY-SA 4.0

from pynput.keyboard import Key, Listener

def on_press(key):
    print('{0} pressed'.format(key))

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
