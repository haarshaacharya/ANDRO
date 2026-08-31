import speech_recognition as sr

WAKE_WORDS = [
    "hey andro",
    "hey android",
    "hey andrew",
    "hello andro",
    "hi andro",
    "ok andro",
    "andro",
]

SLEEP_COMMANDS = [
    "bye andro",
    "goodbye andro",
    "bye bye andro",
    "sleep andro",
    "go to sleep andro",
    "andro sleep",
    "sleep",
    "alvida andro",
    "bye",
    "goodbye",
]

STOP_COMMANDS = [
    "stop andro",
    "stop",
    "ruk jao",
    "ruko",
    "cancel task",
    "abort",
]


class WakeWordListener:
    """Privacy-first wake word detection and voice command listener."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen_for_wake_word(self, timeout: float = 3.0) -> bool:
        """Low-latency audio listener to check if 'Hey ANDRO' is spoken (Privacy-First: no disk storage)."""
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=3.0,
                )
                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN").lower().strip()
                    return any(w in text for w in WAKE_WORDS)
                except (sr.UnknownValueError, sr.RequestError):
                    return False
        except (sr.WaitTimeoutError, Exception):
            return False

    def listen_command(self, timeout: float = 8.0, phrase_time_limit: float = 12.0) -> dict:
        """Listen for an active voice command once ANDRO is in ACTIVE mode."""
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN").strip()
                    return {
                        "success": True,
                        "text": text,
                    }
                except sr.UnknownValueError:
                    return {
                        "success": False,
                        "message": "I couldn't understand the speech.",
                    }
                except sr.RequestError as err:
                    return {
                        "success": False,
                        "message": f"Speech service error: {err}",
                    }
        except sr.WaitTimeoutError:
            return {
                "success": False,
                "timeout": True,
                "message": "Listening timed out with silence.",
            }
        except Exception as err:
            return {
                "success": False,
                "message": f"Microphone error: {err}",
            }

    @staticmethod
    def is_wake_word(text: str) -> bool:
        """Check if a text string contains a wake word."""
        text_lower = text.lower().strip()
        return any(w in text_lower for w in WAKE_WORDS)

    @staticmethod
    def is_sleep_command(text: str) -> bool:
        """Check if a text string requests deactivation / sleep."""
        text_lower = text.lower().strip()
        return any(c == text_lower or text_lower.startswith(c) or c in text_lower for c in SLEEP_COMMANDS)

    @staticmethod
    def is_stop_command(text: str) -> bool:
        """Check if a text string is the emergency STOP command."""
        text_lower = text.lower().strip()
        return any(c == text_lower or text_lower.startswith(c) for c in STOP_COMMANDS)
