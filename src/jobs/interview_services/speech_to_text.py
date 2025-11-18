import openai
from django.conf import settings

class SpeechToTextService:

    @staticmethod
    def transcribe(file_obj):
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-tts",
            file=file_obj,
        )
        return transcript.text
