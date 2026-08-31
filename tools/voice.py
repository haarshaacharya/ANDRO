import speech_recognition as sr

_global_recognizer = sr.Recognizer()
_global_recognizer.pause_threshold = 0.4
_global_recognizer.non_speaking_duration = 0.3
_global_recognizer.energy_threshold = 300
_global_recognizer.dynamic_energy_threshold = True


def listen():
    """Listen to the microphone with ultra-low latency and convert speech to text."""
    with sr.Microphone() as source:
        try:
            # Fast calibration (< 0.15s)
            _global_recognizer.adjust_for_ambient_noise(source, duration=0.15)

            audio = _global_recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=10,
            )

            text = _global_recognizer.recognize_google(
                audio,
                language="en-IN",
            )

            return {
                "success": True,
                "text": text,
            }

        except sr.WaitTimeoutError:
            return {
                "success": False,
                "message": "I didn't hear anything. Please try speaking louder.",
            }

        except sr.UnknownValueError:
            return {
                "success": False,
                "message": "I heard you, but couldn't understand the words.",
            }

        except sr.RequestError as error:
            return {
                "success": False,
                "message": f"Speech recognition service error: {error}",
            }

        except Exception as error:
            return {
                "success": False,
                "message": f"Microphone error: {error}",
            }