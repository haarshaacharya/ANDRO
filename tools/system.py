import subprocess
import shutil
import os
from pathlib import Path


# Safe list of applications ANDRO is allowed to open
APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
    "vscode": ["code"],
    "vs code": ["code"],
}

APP_ALIASES = {
    "google chrome": "chrome",
    "google-chrome": "chrome",
    "browser": "chrome",
    "calc": "calculator",
    "calculator app": "calculator",
    "notes": "notepad",
    "editor": "notepad",
    "text editor": "notepad",
    "file explorer": "explorer",
    "files": "explorer",
    "my computer": "explorer",
    "visual studio code": "vscode",
    "vs code": "vscode",
    "code": "vscode",
    "mspaint": "paint",
    "ms paint": "paint",
}



CHROME_PROFILE = "Profile 1"


def find_chrome():
    """Try common Chrome installation locations."""

    possible_paths = [
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",

        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",

        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    # Try PATH as well
    chrome_in_path = shutil.which("chrome")

    if chrome_in_path:
        return chrome_in_path

    return None


def open_app(app_name: str):
    """Open an allowed application."""

    app_name = app_name.lower().strip()
    app_name = APP_ALIASES.get(app_name, app_name)

    # Special handling for Chrome (uses personal Profile 1)
    if app_name == "chrome":

        chrome_path = find_chrome()

        if chrome_path:
            try:
                subprocess.Popen([chrome_path, f"--profile-directory={CHROME_PROFILE}"])

                return {
                    "success": True,
                    "message": f"Opened Chrome (using {CHROME_PROFILE}) successfully."
                }

            except Exception as error:
                return {
                    "success": False,
                    "message": f"Could not open Chrome: {error}"
                }

        return {
            "success": False,
            "message": "Chrome installation could not be found."
        }

    # Normal allowed apps
    if app_name not in APPS:
        return {
            "success": False,
            "message": f"I don't know how to open '{app_name}' yet."
        }

    command = APPS[app_name][0]

    try:

        # Windows built-in applications
        builtin_apps = [
            "notepad.exe",
            "calc.exe",
            "mspaint.exe",
            "explorer.exe",
        ]

        if command in builtin_apps:
            subprocess.Popen([command])

        elif shutil.which(command):
            subprocess.Popen([command])

        else:
            return {
                "success": False,
                "message": f"'{app_name}' was not found on this computer."
            }

        return {
            "success": True,
            "message": f"Opened {app_name} successfully."
        }

    except Exception as error:
        return {
            "success": False,
            "message": f"Could not open {app_name}: {error}"
        }