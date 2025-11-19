import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from jobs.models import Interview, JobPost
from ..interview_services.llm_service import LLMService
from ..interview_services.text_to_speech import TextToSpeechService
from ..interview_services.conversation import ConversationService

class StartInterviewView(APIView):

    def post(self, request):
        job_id = request.data["job_id"]
        freelancer_id = request.data["freelancer_id"]
        job = JobPost.objects.get(id=job_id)
        conversation_id = ConversationService.conversation()
        interview = Interview.objects.create(
            job_id=job_id,
            freelancer_id=freelancer_id,
            conversation_id=conversation_id
        )
        requirements = f"{job.title}: {job.description} , Required Skills: {', '.join([skill.name for skill in job.required_skills.all()])}"
        first_question = LLMService.generate_first_question(requirements,conversation_id )
        audio_binary = TextToSpeechService.synthesize(first_question)

        return Response({
            "conversation_id": conversation_id,
            "first_question_text": first_question,
            "first_question_audio_base64": base64.b64encode(audio_binary).decode()
        })
