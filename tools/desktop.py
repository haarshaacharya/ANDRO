import time
from datetime import datetime
from pathlib import Path
import pyautogui
import pyperclip

# Safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Directory to store screenshots
SCREENSHOTS_DIR = Path.home() / "Pictures" / "ANDRO_Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Safe keyboard key aliases
KEY_ALIASES = {
    "enter": "enter",
    "return": "enter",
    "esc": "escape",
    "escape": "escape",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "delete": "delete",
    "del": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "pageup": "pageup",
    "pagedown": "pagedown",
    "home": "home",
    "end": "end",
    "f5": "f5",
    "f11": "f11",
    "f12": "f12",
    "win": "win",
    "windows": "win",
    "capslock": "capslock",
}


def type_text(text: str):
    """Type text into the currently focused window using clipboard paste."""
    text = str(text)
    if not text:
        return {
            "success": False,
            "message": "No text was provided to type.",
        }

    try:
        # Use clipboard for reliable Unicode, special characters, and emojis
        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        return {
            "success": True,
            "message": f"Typed text: '{text}'",
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not type text: {error}",
        }


def press_key(key: str):
    """Press a single keyboard key safely."""
    key = str(key).lower().strip()
    if not key:
        return {
            "success": False,
            "message": "Please specify a key to press.",
        }

    normalized_key = KEY_ALIASES.get(key, key)

    try:
        pyautogui.press(normalized_key)
        return {
            "success": True,
            "message": f"Pressed key '{key}'.",
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not press key '{key}': {error}",
        }


def keyboard_shortcut(shortcut: str):
    """Execute a keyboard shortcut (e.g., 'ctrl+c', 'ctrl+v', 'ctrl+l', 'alt+tab')."""
    shortcut = str(shortcut).lower().strip()
    if not shortcut:
        return {
            "success": False,
            "message": "Please specify a shortcut combination.",
        }

    # Normalize separators (+, -, or space)
    raw_keys = shortcut.replace("-", "+").replace(" ", "+").split("+")
    keys = [k.strip() for k in raw_keys if k.strip()]

    # Normalize individual key aliases
    normalized_keys = [KEY_ALIASES.get(k, k) for k in keys]

    try:
        pyautogui.hotkey(*normalized_keys)
        return {
            "success": True,
            "message": f"Executed shortcut '{shortcut}'.",
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not execute shortcut '{shortcut}': {error}",
        }


def take_screenshot(filename: str = ""):
    """Capture full screen and save as timestamped image."""
    try:
        from tools.vision import capture_screen_safely
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if filename:
            clean_name = filename if filename.endswith(".png") else f"{filename}.png"
        else:
            clean_name = f"screenshot_{timestamp}.png"

        save_path = SCREENSHOTS_DIR / clean_name
        success = capture_screen_safely(str(save_path))

        if success and save_path.exists():
            return {
                "success": True,
                "message": f"Screenshot saved: {clean_name} (in Pictures/ANDRO_Screenshots)",
                "path": str(save_path),
            }
        else:
            return {
                "success": False,
                "message": "Could not capture screenshot. Run 'pip install pillow' to enable screenshot support.",
            }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not take screenshot: {error}",
        }


def mouse_click(button: str = "left", clicks: int = 1):
    """Click mouse button safely."""
    button = str(button).lower().strip()
    if button not in ["left", "right", "middle"]:
        button = "left"

    try:
        pyautogui.click(button=button, clicks=clicks)
        return {
            "success": True,
            "message": f"Clicked {button} mouse button ({clicks}x).",
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not click mouse: {error}",
        }


def mouse_move(x: int, y: int):
    """Move mouse cursor swiftly to coordinates (x, y)."""
    try:
        x, y = int(x), int(y)
        pyautogui.moveTo(x, y, duration=0.1)
        return {
            "success": True,
            "message": f"Moved mouse to ({x}, {y}).",
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not move mouse: {error}",
        }
