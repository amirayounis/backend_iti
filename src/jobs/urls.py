from rest_framework.routers import DefaultRouter
from django.urls import path, include

from jobs.interview_views.cleint_views.job_proposals import JobPropsalView
from jobs.interview_views.cleint_views.propsaleupade import PropsalUpdateView
from .views import (
    SkillViewSet, FreelancerProfileViewSet, ClientProfileViewSet,
    JobPostViewSet, post_proposal,ProposalViewSet, post_job, FreelancerPortfolioViewSet, get_interview_details
)
from .interview_views.start_interview import StartInterviewView
from .interview_views.message_interview import InterviewMessageView
from .interview_views.stop_interview import StopInterviewView
from .interview_views.end_interview import EndInterviewView

router = DefaultRouter()
router.register(r'skills', SkillViewSet)
router.register(r'freelancer-profiles', FreelancerProfileViewSet)
router.register(r'client-profiles', ClientProfileViewSet)
router.register(r'jobs', JobPostViewSet)
router.register(r'proposals', ProposalViewSet)
router.register(r'freelancer-portfolios', FreelancerPortfolioViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('post-proposal/', post_proposal, name='post_proposal'),
    path("start/", StartInterviewView.as_view()),
    path("message/", InterviewMessageView.as_view()),
    path("stop/", StopInterviewView.as_view()),
    path("end/", EndInterviewView.as_view()),
    path('job-proposals/', JobPropsalView.as_view()),
    path('proposal-update/', PropsalUpdateView.as_view()),
    path('interview/', get_interview_details, name='get_interview_details'),
]