from datetime import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Interview

class StopInterviewView(APIView):

    def post(self, request):
        conversation_id = request.data["conversation_id"]
        interview = Interview.objects.get(conversation_id=conversation_id)
        interview.status = "stopped"
        interview.ended_at = timezone.now()
        interview.save()
        return Response({"status": "interview stopped"})
