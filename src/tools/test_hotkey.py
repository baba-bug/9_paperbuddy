import keyboard
import time
import sys

def on_trigger():
    print("🔥 Hotkey Triggered!")

hotkey = "ctrl+alt+shift+capslock+p"
# hotkey = "ctrl+alt+p" # simpler fallback

print(f"Listening for {hotkey}...")
print("Press ESC to quit.")

try:
    keyboard.add_hotkey(hotkey, on_trigger)
    keyboard.wait('esc')
except ImportError:
    print("Keyboard module not found?")
except Exception as e:
    print(f"Error: {e}")
