import io
import openai
from django.conf import settings

class SpeechToTextService:

    @staticmethod
    def transcribe(file_obj):
        try:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set")

            client = openai.OpenAI(api_key=api_key)
            print("Preparing file for transcription")
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
            print(file_param)
            # Use a speech transcription model (e.g. 'whisper-1')
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=file_param,

            )
            print(transcript)
            return transcript.text
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            raise
# language="en"