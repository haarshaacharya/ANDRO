import io
import os
import tempfile
import subprocess
from pathlib import Path
import ollama

# Preferred Ollama vision models in order of priority
VISION_MODELS = [
    "llava",
    "llava:latest",
    "llava:7b",
    "moondream",
    "moondream:latest",
    "qwen2.5-vl",
    "bakllava",
    "llama3.2-vision",
]

CONFIGURED_VISION_MODEL = "llava"


def capture_screen_safely(output_path: str) -> bool:
    """Capture full screen safely using PIL if available, or native Windows .NET without dependencies."""
    # Method 1: Try PIL if installed
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        screenshot.save(output_path)
        return True
    except Exception:
        pass

    # Method 2: Try PyAutoGUI if available
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(output_path)
        return True
    except Exception:
        pass

    # Method 3: Native Windows PowerShell .NET Screen Capture (Zero Dependencies)
    try:
        norm_path = output_path.replace("\\", "/")
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
            "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
            "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
            "$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size); "
            f"$bmp.Save('{norm_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
            "$graphics.Dispose(); "
            "$bmp.Dispose();"
        )
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, creationflags=flags)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception:
        pass

    return False


def get_available_vision_model():
    """Find the first available vision model installed in local Ollama."""
    try:
        models_response = ollama.list()
        models_list = getattr(models_response, "models", None) or models_response.get("models", [])
        installed_names = []
        for m in models_list:
            name = getattr(m, "model", None) or getattr(m, "name", None) or (m.get("name") if isinstance(m, dict) else "")
            if name:
                installed_names.append(str(name).lower())

        for v_model in VISION_MODELS:
            for inst in installed_names:
                if inst.startswith(v_model):
                    return inst

        for inst in installed_names:
            if CONFIGURED_VISION_MODEL in inst:
                return inst
    except Exception:
        pass
    return None


def analyze_screen(prompt: str = ""):
    """Capture a single on-demand screenshot and analyze visible screen contents or errors."""
    if not prompt:
        prompt = (
            "Analyze the attached screenshot of the computer screen. "
            "Describe the visible application, active windows, text, messages, "
            "and any error codes or dialog boxes clearly and concisely."
        )

    temp_path = None
    try:
        # Step 1: Capture one single screenshot on demand
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            temp_path = tmp_file.name

        captured = capture_screen_safely(temp_path)
        if not captured or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return {
                "success": False,
                "message": "Could not capture the screen image. Run 'pip install pillow' to enable screenshot support.",
            }

        # Step 2: Check for installed vision model in Ollama
        vision_model = get_available_vision_model()

        if vision_model:
            with open(temp_path, "rb") as img_f:
                image_bytes = img_f.read()

            response = ollama.chat(
                model=vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_bytes],
                    }
                ],
            )
            content = response.message.content.strip()
            return {
                "success": True,
                "message": content,
                "model_used": vision_model,
            }
        else:
            return {
                "success": True,
                "message": (
                    "I captured your screen, but a vision-capable AI model is not yet installed in Ollama.\n\n"
                    "💡 To enable full AI Screen Vision, open your terminal and run:\n"
                    "   ollama pull llava\n"
                    "   (or: ollama pull moondream)\n\n"
                    "Once downloaded, I will be able to visually inspect your screen and explain errors!"
                ),
                "model_used": None,
            }

    except Exception as error:
        return {
            "success": False,
            "message": f"Could not analyze the screen: {error}",
        }
    finally:
        # Step 3: Strictly clean up temporary screenshot immediately (Privacy Rule)
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
