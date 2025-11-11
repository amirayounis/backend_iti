from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response


from users.models import User
from .models import Skill, FreelancerProfile, ClientProfile, JobPost, Proposal
from .serializers import (
    SkillSerializer, FreelancerProfileSerializer, ClientProfileSerializer,
    JobPostSerializer, ProposalSerializer
)
from .ai.job_matching import get_matches_jops, store_job_embedding , remove_job_embedding,store_job_embedding_with_ollama,get_matches_jops_ollama
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
        full_description = f"{title}\n\n{description}\n\nSkills: {','.join(skills_list)}"
        store_job_embedding_with_ollama( job_id=serializer.instance.id, description=full_description)
    
    @action(detail=False, methods=['get'], url_path='matched-jobs')
    def matched_jobs(self, request):
        """Return matched jobs for the current freelancer."""
        user = request.user
        print ("uuuuuuuuuuuuuser",user)
        # Ensure the user has a freelancer profile
        try:
            freelancer_profile = FreelancerProfile.objects.get(user=user)
        except AttributeError:
            return Response(
                {"detail": "No freelancer profile found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
        # Combine all freelancer skill descriptions into a single query text
        query_text = "the skills are: " + ",".join(skill.name for skill in freelancer_profile.skills.all())
        query_text += f", field is: {freelancer_profile.categories_of_expertise}, experience years: {freelancer_profile.experience_years}"
        print("query_text",query_text)
        job_list=get_matches_jops_ollama(query_text)
        print("job_list",job_list)
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
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'freelancerprofile'):
            return Proposal.objects.filter(freelancer=user.freelancerprofile)
        elif hasattr(user, 'clientprofile'):
            return Proposal.objects.filter(job__client=user.clientprofile)
        return Proposal.objects.none()

    @action(detail=True, methods=['post'])
    def generate_ai_suggestion(self, request, pk=None):

        """
        Generate AI-powered suggestions for a proposal.
        Analyzes the match between the freelancer's profile and the job requirements.
        """
        proposal = self.get_object()
        
        try:
            from .ai.job_matching import find_matching_jobs
            
            # Get freelancer's skills and experience
            freelancer_profile = proposal.freelancer
            skills = [skill.name for skill in freelancer_profile.skills.all()]
            experience = freelancer_profile.experience_years
            
            # Find matching score
            matches = find_matching_jobs(
                freelancer_skills=skills,
                experience_years=experience,
                n_results=1
            )
            
            if matches and matches[0]['job_id'] == str(proposal.job.id):
                match = matches[0]
                # Convert distance to similarity score (1 - normalized_distance)
                score = 1 - (match['relevance_score'] or 0) if match['relevance_score'] is not None else 0.5
                
                # Generate feedback based on score
                if score >= 0.8:
                    feedback = "Excellent match! Your skills and experience align very well with the job requirements."
                elif score >= 0.6:
                    feedback = "Good match. You have most of the required skills, but there might be some areas for improvement."
                else:
                    feedback = "Fair match. Consider highlighting relevant experience or acquiring additional skills for this role."
                
                ai_feedback = {
                    'score': score,
                    'feedback': feedback,
                    'match_details': match
                }
                
                proposal.ai_suggestion_score = score
                proposal.ai_feedback = feedback
                proposal.save()
                
                return Response(ai_feedback, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Could not analyze job match accurately'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error generating AI suggestion: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
def post_job(request):
    cleint=request.user
    JobPostSerializer=JobPostSerializer(data=request.data)
    if JobPostSerializer.is_valid():
        JobPostSerializer.save(client=cleint)
        return Response({"data":JobPostSerializer.data,"is_success":True}, status=status.HTTP_201_CREATED)