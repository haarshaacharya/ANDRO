import io
import os
import base64
import tempfile
from pathlib import Path
import pyautogui
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

# Active vision model configuration (can be customized)
CONFIGURED_VISION_MODEL = "llava"


def get_available_vision_model():
    """Find the first available vision model installed in local Ollama."""
    try:
        models_response = ollama.list()
        # Handle both dict and object structures
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

        # Also check configured model
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
        screenshot = pyautogui.screenshot()

        # Save to a temporary image file for processing
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            temp_path = tmp_file.name
            screenshot.save(temp_path)

        # Step 2: Check for installed vision model in Ollama
        vision_model = get_available_vision_model()

        if vision_model:
            # Query Ollama vision model with the image
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
            # Vision model not yet downloaded - provide a friendly, helpful guide
            return {
                "success": True,
                "message": (
                    "I captured the screen, but a vision-capable AI model is not yet installed in Ollama.\n"
                    "💡 To enable full AI Screen Vision, open your terminal and run:\n"
                    "   ollama pull llava\n"
                    "   (or: ollama pull moondream)\n"
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
