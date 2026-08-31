import threading
import pyttsx3
from tools.state_manager import state_manager


def _run_speak(text: str):
    """Speak text using SAPI5 engine in thread and manage speaking state."""
    state_manager.start_speaking()
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        engine = pyttsx3.init()
        engine.setProperty("rate", 205)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass
    finally:
        state_manager.stop_speaking()


def speak(text: str):
    """Make ANDRO speak text asynchronously with state tracking to prevent echo."""
    text = str(text).strip()
    if not text:
        return

    thread = threading.Thread(target=_run_speak, args=(text,), daemon=True)
    thread.start()