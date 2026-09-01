import re
import speech_recognition as sr
from tools.logger import log_activity
from tools.state_manager import state_manager, AssistantState

# Phrases that should NEVER trigger wake word
BLOCKED_PHRASES = [
    "android development",
    "android studio",
    "android phone",
    "android app",
    "android apps",
    "android device",
    "android os",
    "android version",
    "android project",
    "android code",
    "android tutorial",
    "android course",
    "android kotlin",
    "android java",
    "android auto",
    "android tv",
]

# Strict wake word patterns
WAKE_PATTERNS = [
    r"^hey\s+andro\b",
    r"^hello\s+andro\b",
    r"^hi\s+andro\b",
    r"^ok\s+andro\b",
    r"^okay\s+andro\b",
    r"^hey\s+android$",
    r"^hello\s+android$",
    r"^andro$",
]

SLEEP_PATTERNS = [
    r"\bbye\s+andro\b",
    r"\bgoodbye\s+andro\b",
    r"\bsleep\s+andro\b",
    r"\bgo\s+to\s+sleep\s+andro\b",
    r"\bgo\s+to\s+sleep\b",
    r"\bandro\s+sleep\b",
    r"\balvida\s+andro\b",
    r"^bye$",
    r"^goodbye$",
]

STOP_PATTERNS = [
    r"^stop\s+andro$",
    r"^stop$",
    r"^ruk\s+jao$",
    r"^ruko$",
    r"^cancel\s+task$",
    r"^abort$",
]

EXIT_PATTERNS = [
    r"\bexit\s+andro\b",
    r"\bclose\s+andro\b",
    r"\bshutdown\s+andro\b",
    r"\bandro\s+exit\b",
    r"\bandro\s+close\b",
    r"\bandro\s+shutdown\b",
    r"^exit$",
    r"^close$",
    r"^shutdown$",
    r"^quit$",
    r"\bband\s+karo\s+andro\b",
    r"\bandro\s+band\s+karo\b",
    r"\bband\s+kar\s+do\s+andro\b",
    r"\bandro\s+band\s+kar\s+do\b",
]


def normalize_speech(text: str) -> str:
    """Clean speech text: lowercase, remove punctuation, collapse whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


class WakeWordListener:
    """Privacy-first wake word detection with strict matching and speech-echo prevention."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.4
        self.recognizer.non_speaking_duration = 0.25
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen_for_wake_word(self, timeout: float = 2.5) -> bool:
        """Low-latency audio listener for 'Hey ANDRO' in SLEEPING mode."""
        state_manager.wait_after_speech(0.25)

        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=2.5,
                )
                try:
                    raw_text = self.recognizer.recognize_google(audio, language="en-IN")
                    norm_text = normalize_speech(raw_text)

                    if self.is_wake_word(norm_text):
                        log_activity("WAKE_WORD", f"Wake phrase detected: '{raw_text}'")
                        return True
                except (sr.UnknownValueError, sr.RequestError):
                    return False
        except (sr.WaitTimeoutError, Exception):
            return False

        return False

    def listen_command(self, timeout: float = 7.0, phrase_time_limit: float = 10.0) -> dict:
        """Listen for an active voice command once ANDRO is in ACTIVE mode."""
        state_manager.wait_after_speech(0.35)

        try:
            with sr.Microphone() as source:
                state_manager.set_state(AssistantState.LISTENING, "Listening for your voice...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
                try:
                    raw_text = self.recognizer.recognize_google(audio, language="en-IN").strip()
                    log_activity("VOICE_INPUT", f"Recognized: '{raw_text}'")
                    return {
                        "success": True,
                        "text": raw_text,
                    }
                except sr.UnknownValueError:
                    return {
                        "success": False,
                        "message": "I couldn't understand the speech.",
                    }
                except sr.RequestError as err:
                    log_activity("ERROR", f"Speech service error: {err}")
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
            log_activity("ERROR", f"Microphone error: {err}")
            return {
                "success": False,
                "message": f"Microphone error: {err}",
            }

    @staticmethod
    def is_wake_word(text: str) -> bool:
        """Strict wake word matching to reject false positives like 'Android development'."""
        norm = normalize_speech(text)
        if not norm:
            return False

        # Reject blocked phrases
        for blocked in BLOCKED_PHRASES:
            if blocked in norm:
                return False

        # Match approved wake patterns
        for pattern in WAKE_PATTERNS:
            if re.search(pattern, norm):
                return True

        return False

    @staticmethod
    def is_sleep_command(text: str) -> bool:
        """Check if a text string strictly requests deactivation / sleep."""
        norm = normalize_speech(text)
        for pattern in SLEEP_PATTERNS:
            if re.search(pattern, norm):
                return True
        return False

    @staticmethod
    def is_stop_command(text: str) -> bool:
        """Check if a text string is the emergency STOP command."""
        norm = normalize_speech(text)
        for pattern in STOP_PATTERNS:
            if re.search(pattern, norm):
                return True
        return False

    @staticmethod
    def is_exit_command(text: str) -> bool:
        """Check if a text string is an EXIT / SHUTDOWN command."""
        norm = normalize_speech(text)
        for pattern in EXIT_PATTERNS:
            if re.search(pattern, norm):
                return True
        return False

