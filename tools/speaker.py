import threading
import pyttsx3


def _run_speak(text: str):
    """Speak text using SAPI5 engine in thread."""
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def speak(text):
    """Make ANDRO speak text asynchronously for instant sub-second actions."""
    text = str(text).strip()
    if not text:
        return

    thread = threading.Thread(target=_run_speak, args=(text,), daemon=True)
    thread.start()