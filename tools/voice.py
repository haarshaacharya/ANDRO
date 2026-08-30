import speech_recognition as sr


def listen():
    """Listen to the microphone and convert speech to text."""

    recognizer = sr.Recognizer()

    # Make recognition less sensitive to timeout
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:

        print("\n🎤 ANDRO is preparing microphone...")
        print("🔇 Adjusting for background noise...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1
        )

        print("\n🎤 ANDRO is listening...")
        print("🗣️ Speak now!\n")

        try:

            audio = recognizer.listen(
                source,
                timeout=15,
                phrase_time_limit=15
            )

            print("🧠 Processing voice...")

            text = recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            return {
                "success": True,
                "text": text
            }

        except sr.WaitTimeoutError:

            return {
                "success": False,
                "message": "I didn't hear anything. Please try speaking louder."
            }

        except sr.UnknownValueError:

            return {
                "success": False,
                "message": "I heard you, but couldn't understand the words."
            }

        except sr.RequestError as error:

            return {
                "success": False,
                "message": f"Speech recognition service error: {error}"
            }

        except Exception as error:

            return {
                "success": False,
                "message": f"Microphone error: {error}"
            }