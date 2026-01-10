import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from jobs.models import Interview
from ..interview_services.speech_to_text import SpeechToTextService

class recored(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        audio_file = request.FILES.get("audio_file")
        # 1. STT
        print("Starting speech-to-text transcription")
        user_text = SpeechToTextService.transcribe(audio_file)
        # store text into txt file with UTF-8 encoding to support Arabic and other languages
        with open("recorded_text.txt", "a", encoding="utf-8") as f:
            f.write(user_text + "\n")   
            print(f"Transcription result: {user_text}")
        return Response({
            "user_text": user_text,
        })