import speech_recognition as sr  # type: ignore


class SpeechService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def get_speech_input(self):
        """Get speech input from user."""
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None
