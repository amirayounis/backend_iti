import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Interview
from ..interview_services.speech_to_text import SpeechToTextService

class generate_report(APIView):

    def post(self, request):
        audio_file = request.FILES.get("audio_file")
        # 1. STT
        print("Starting speech-to-text transcription")
        user_text = SpeechToTextService.transcribe(audio_file)
        # store text into txt file
        with open("recorded_text.txt", "a") as f:
            f.write(user_text + "\n")   
            print(f"Transcription result: {user_text}")
        return Response({
            "user_text": user_text,
        })