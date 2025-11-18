import openai
import base64
from django.conf import settings

class TextToSpeechService:

    @staticmethod
    def synthesize(text):
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        result = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text,
        )

        # result is binary audio
        return result.read()  
