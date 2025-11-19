import io
import openai
from django.conf import settings

class SpeechToTextService:

    @staticmethod
    def transcribe(file_obj):
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        # The OpenAI client expects `file` to be bytes, a file-like IO, PathLike or a tuple.
        # Django provides `InMemoryUploadedFile` / `TemporaryUploadedFile` objects, so
        # convert them to a tuple (filename, bytes, content_type) which the SDK accepts.
        if hasattr(file_obj, "read"):
            # read bytes from the uploaded file
            file_bytes = file_obj.read()
            # try to rewind original file if possible
            try:
                file_obj.seek(0)
            except Exception:
                pass
            filename = getattr(file_obj, "name", "audio")
            content_type = getattr(file_obj, "content_type", None)
            file_param = (filename, file_bytes, content_type)
        else:
            file_param = file_obj

        # Use a speech transcription model (e.g. 'whisper-1')
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file_param,
            language="en"
        )

        return transcript.text
