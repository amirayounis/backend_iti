import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Interview
from ..interview_services.speech_to_text import SpeechToTextService
from ..interview_services.llm_service import LLMService
from ..interview_services.text_to_speech import TextToSpeechService

class InterviewMessageView(APIView):

    def post(self, request):
        conversation_id = request.data["conversation_id"]
        audio_file = request.FILES.get("audio_file")

        # 1. STT
        user_text = SpeechToTextService.transcribe(audio_file)

        # 2. Get next question
        next_question = LLMService.generate_next_question(user_text, conversation_id)

        # 3. TTS
        audio_binary = TextToSpeechService.synthesize(next_question)

        return Response({
            "user_text": user_text,
            "ai_text": next_question,
            "ai_audio_base64": base64.b64encode(audio_binary).decode()
        })
