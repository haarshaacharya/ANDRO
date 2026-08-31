import os
import threading
from datetime import datetime
from pathlib import Path

# Logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_log_lock = threading.Lock()


def get_daily_log_file() -> Path:
    """Get the path to today's log file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return LOGS_DIR / f"andro_{date_str}.log"


def log_activity(category: str, message: str, details: str = None):
    """Write an event or error to the local daily log file in a thread-safe manner."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] [{category.upper()}] {message}"
    if details:
        entry += f" | Details: {details}"
    entry += "\n"

    try:
        with _log_lock:
            log_file = get_daily_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)
    except Exception:
        pass
