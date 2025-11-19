import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import FreelancerProfile, Interview, JobPost, Proposalai

class PropsalUpdateView(APIView):

    def post(self, request):
        proposal_id = request.data["proposal_id"]
        status = request.data["status"]
        proposal=Proposalai.objects.get(id=proposal_id)
        job=JobPost.objects.get(id=proposal.job_id)
        proposals_job=Proposalai.objects.filter(job_id=job.id)
        if status=="accepted":
            proposal.status="accepted"
            proposal.save()
            job.status="ongoing"
            job.save()
            #reject other proposals
            for prop in proposals_job:
                if prop.id!=proposal.id:
                    prop.status="rejected"
                    prop.save()
        elif status=="rejected":
            proposal.status="rejected"
            proposal.save()
        return Response({"message": "Proposal status updated successfully."})