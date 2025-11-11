from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    SkillViewSet, FreelancerProfileViewSet, ClientProfileViewSet,
    JobPostViewSet, ProposalViewSet, post_job
)

router = DefaultRouter()
router.register(r'skills', SkillViewSet)
router.register(r'freelancer-profiles', FreelancerProfileViewSet)
router.register(r'client-profiles', ClientProfileViewSet)
router.register(r'jobs', JobPostViewSet)
router.register(r'proposals', ProposalViewSet)

urlpatterns = [
    path('', include(router.urls))]