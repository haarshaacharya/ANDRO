import pyttsx3


engine = pyttsx3.init()

# Speech speed
engine.setProperty("rate", 175)

# Volume: 0.0 to 1.0
engine.setProperty("volume", 1.0)


def speak(text):
    """Make ANDRO speak text."""

    text = str(text)

    print(f"\n🗣️ ANDRO is speaking...")

    engine.say(text)
    engine.runAndWait()