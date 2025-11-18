from httpcore import request
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from jobs.ai.draft_proposal import draft_proposal
from users.models import User
from .models import FreelancerPortfolio, Skill, FreelancerProfile, ClientProfile, JobPost, Proposalai
from .serializers import (
    FreelancerPortfolioSerializer, SkillSerializer, FreelancerProfileSerializer, ClientProfileSerializer,
    JobPostSerializer, ProposalSerializer
)
from .ai.job_matching import get_matches_jobs, store_job_embedding , remove_job_embedding
class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class FreelancerProfileViewSet(viewsets.ModelViewSet):
    queryset = FreelancerProfile.objects.all()
    serializer_class = FreelancerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FreelancerProfile.objects.filter(user=self.request.user)
    def create(self, request, *args, **kwargs):
        print("POST request received in FreelancerProfileViewSet")

        data = request.data.copy()
        skills_data = data.pop('skills', [])
        print("Skills data:", skills_data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Save profile without skills first
        freelancer=FreelancerProfile.objects.get(user=request.user)
        profile = serializer.update(instance=freelancer, validated_data=data)

        # Handle ManyToMany skills
        for skill_item in skills_data:
            print("Skills data:", skill_item)
            # If skills are strings
            if isinstance(skill_item, str):
                skill_name = skill_item.lower()
            # If skills are dicts (e.g., {"name": "Python"})
            elif isinstance(skill_item, dict):
                skill_name = skill_item.get('name', '').lower()
            else:
                continue

            if skill_name:
                skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
                profile.skills.add(skill_obj)

        response_serializer = self.get_serializer(profile)
        data_prof=response_serializer.data
        data_prof['skills']=[skill.name for skill in profile.skills.all()]
        response_serializer._data = data_prof
        return Response({"data":response_serializer.data,"is_success":True}, status=status.HTTP_201_CREATED)

class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ClientProfile.objects.filter(user=self.request.user)

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        client_profile = self.request.user
        serializer.save(client=client_profile)
        # store  jop description+ jops tittle +skilles  on vector db
        serializered_instance = serializer.instance
        title=serializered_instance.title
        description=serializered_instance.description
        Skills=serializered_instance.required_skills.all()
        skills_list=[skill.name for skill in Skills]
        full_description = (
        f"Job Title: {title}. "
        f"Job Description: {description}. "
        f"Required Skills: {', '.join(skills_list)}.")
        store_job_embedding( job_id=serializer.instance.id, description=full_description)
    
    @action(detail=False, methods=['get'], url_path='matched-jobs')
    def matched_jobs(self, request):
        """Return matched jobs for the current freelancer."""
        user = request.user
        print("uuuuuuuuuuuuuser", user)

    # Ensure the user has a freelancer profile
        try:
            freelancer_profile = FreelancerProfile.objects.get(user=user)
        except FreelancerProfile.DoesNotExist:
            return Response(
                {"detail": "No freelancer profile found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
    # -------------------------------
    # Build structured embedding query
    # -------------------------------
        skills_str = ", ".join(skill.name for skill in freelancer_profile.skills.all())
        query_text = f"""
    Skills:
    {skills_str}
    Field:
    {freelancer_profile.categories_of_expertise}
    """

        print("Structured Query:", query_text)

        # Perform semantic job matching
        job_list = get_matches_jobs(query_text,current_user=user)

        return Response(job_list, status=status.HTTP_200_OK)
    def perform_destroy(self, instance):
        client=self.request.user
        print("instance.client",instance.client)
        # if instance.client !=client:
        #     print("You do not have permission to delete this job.")
        #     return Response("You do not have permission to delete this job.", status=status.HTTP_403_FORBIDDEN)
        # Remove job embedding from vector database
        remove_job_embedding(job_id=instance.id)
        # Delete the job post
        instance.delete()

    # @action(detail=True, methods=['post'])
    # def generate_ai_criteria(self, request, pk=None):
    #     """
    #     Generate AI-powered criteria suggestions for a job posting.
    #     This endpoint analyzes the job description and suggests relevant skills,
    #     experience requirements, and other criteria.
    #     """
    #     job = self.get_object()
        
    #     try:
    #         from .ai.job_matching import generate_job_criteria, store_job_embedding
            
    #         # Generate AI criteria
    #         # ai_criteria = generate_job_criteria(job.description)
    #         # Store job in vector database for matching
    #         # store_job_embedding(
    #         #     job_id=job.id,
    #         #     title=job.title,
    #         #     description=job.description
    #         # )
            
    #         # Update job with AI suggestions
    #         # job.ai_generated_criteria = ai_criteria
    #         job.save()
            
    #         return Response(ai_criteria, status=status.HTTP_200_OK)
            
    #     except Exception as e:
    #         return Response(
    #             {'error': f'Error generating AI criteria: {str(e)}'},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposalai.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    # def get_queryset(self):
    #     user = self.request.user
    #     if hasattr(user, 'freelancerprofile'):
    #         return Proposalai.objects.filter(freelancer=user.freelancerprofile)
    #     elif hasattr(user, 'clientprofile'):
    #         return Proposalai.objects.filter(job__client=user.clientprofile)
    #     return Proposalai.objects.none()    
def post_job(request):
    cleint=request.user
    JobPostSerializer=JobPostSerializer(data=request.data)
    if JobPostSerializer.is_valid():
        JobPostSerializer.save(client=cleint)
        return Response({"data":JobPostSerializer.data,"is_success":True}, status=status.HTTP_201_CREATED)
class FreelancerPortfolioViewSet(viewsets.ModelViewSet):
    queryset = FreelancerPortfolio.objects.all()
    serializer_class = FreelancerPortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FreelancerPortfolio.objects.filter(user__user=self.request.user)

    def perform_create(self, serializer):
        try:
            freelancer_profile = FreelancerProfile.objects.get(user=self.request.user)
        except FreelancerProfile.DoesNotExist:
            raise serializers.ValidationError("Freelancer profile not found.")
        serializer.save(user=freelancer_profile)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def post_proposal(request):
    """Create a draft proposal for a job"""
    try:
        freelancer = request.user.freelancerprofile
    except FreelancerProfile.DoesNotExist:
        return Response(
            {"data": None, "is_success": False, "error": "No freelancer profile found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    job_id = request.data.get('job_id')
    if not job_id:
        return Response(
            {"data": None, "is_success": False, "error": "job_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        job = JobPost.objects.get(id=job_id)
    except JobPost.DoesNotExist:
        return Response(
            {"data": None, "is_success": False, "error": "Job not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Draft the proposal
    proposal_obj = draft_proposal(job, freelancer)
    
    if not proposal_obj:
        return Response(
            {"data": None, "is_success": False, "error": "Failed to create proposal"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Serialize and return the created proposal
    response_serializer = ProposalSerializer(proposal_obj)
    return Response(
        {"data": response_serializer.data, "is_success": True},
        status=status.HTTP_201_CREATED
    )