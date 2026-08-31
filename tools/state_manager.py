import time
import threading
from enum import Enum
from tools.logger import log_activity


class AssistantState(str, Enum):
    SLEEPING = "SLEEPING"
    ACTIVE = "ACTIVE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"


class StateManager:
    """Thread-safe state manager for ANDRO to coordinate speech, listening, and prevent echo loops."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = AssistantState.SLEEPING
        self._is_speaking = False
        self._last_speech_time = 0.0
        self._state_listeners = []

    def add_listener(self, callback):
        """Add a listener for state changes (e.g. GUI state badge updates)."""
        with self._lock:
            if callback not in self._state_listeners:
                self._state_listeners.append(callback)

    def get_state(self) -> AssistantState:
        with self._lock:
            return self._state

    def set_state(self, new_state: AssistantState, detail: str = ""):
        with self._lock:
            old_state = self._state
            self._state = new_state
            listeners = list(self._state_listeners)

        if old_state != new_state:
            log_activity("STATE", f"{old_state} -> {new_state}", detail)

        for listener in listeners:
            try:
                listener(new_state, detail)
            except Exception:
                pass

    def start_speaking(self):
        """Set speaking flag to True and transition state to SPEAKING."""
        with self._lock:
            self._is_speaking = True
        self.set_state(AssistantState.SPEAKING, "ANDRO is speaking...")

    def stop_speaking(self):
        """Set speaking flag to False and record the timestamp for post-speech cooldown."""
        with self._lock:
            self._is_speaking = False
            self._last_speech_time = time.time()

    def is_speaking(self) -> bool:
        with self._lock:
            return self._is_speaking

    def wait_after_speech(self, cooldown_seconds: float = 0.8):
        """Wait briefly after speech finishes to prevent microphone from picking up residual audio."""
        while self.is_speaking():
            time.sleep(0.05)

        with self._lock:
            elapsed = time.time() - self._last_speech_time

        if elapsed < cooldown_seconds:
            time.sleep(cooldown_seconds - elapsed)


# Global singleton instance
state_manager = StateManager()
