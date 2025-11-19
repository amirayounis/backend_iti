import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import FreelancerProfile, Interview, JobPost, Proposalai

class JobPropsalView(APIView):

    def post(self, request):
        job_id = request.data["job_id"]
        propsals = Proposalai.objects.filter(job_id=job_id)
        proposals_data=[]
        for proposal in propsals:
            freelancer=proposal.freelancer
            interview=Interview.objects.filter(job_id=job_id,freelancer=freelancer).first()
            interview_score=-1
            if interview:
                interview_score=interview.score
            freelancer_profile=FreelancerProfile.objects.get(user=freelancer)
            freelancer_card={
                "freelancer_name": freelancer.username,
                "freelancer_location": freelancer_profile.preferred_location,
                "exprience_level": freelancer_profile.experience_years,
                "skills":[  skill.name for skill in freelancer_profile.skills.all()],
                "hourly_rate": freelancer_profile.hourly_rate,
                "ai_match_score":proposal.match_score,
                "duration":proposal.duration_in_days,
                "proposal_id":proposal.id,
                "freelancer_id":freelancer.id,
                "interview_score":interview_score,
            }
            proposals_data.append(freelancer_card)
        return Response(proposals_data)