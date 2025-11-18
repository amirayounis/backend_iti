from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    SkillViewSet, FreelancerProfileViewSet, ClientProfileViewSet,
    JobPostViewSet, post_proposal,ProposalViewSet, post_job, FreelancerPortfolioViewSet
)

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
]