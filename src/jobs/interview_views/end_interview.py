from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Interview
from ..interview_services.report_generator import ReportGenerator
from ..interview_services.conversation import ConversationService

class EndInterviewView(APIView):

    def post(self, request):
        conversation_id = request.data["conversation_id"]
        interview = Interview.objects.get(conversation_id=conversation_id)
        items = ConversationService.get_conversation(conversation_id)
        # build transcript text
        transcript = ""
        for msg in items:
            transcript += f"{msg.role.upper()}: {msg.content[0].text}\n"

        report_data = ReportGenerator.generate_report(
            job_requirements=interview.job.requirements,
            transcript=transcript
        )

        interview.score = report_data["score"]
        interview.report = report_data["summary"]
        interview.status = "finished"
        interview.save()

        return Response(report_data)
