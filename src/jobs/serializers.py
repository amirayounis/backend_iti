from rest_framework import serializers
from .models import Skill, FreelancerProfile, ClientProfile, JobPost, Proposal

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class FreelancerProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FreelancerProfile
        exclude = ['user','skills']
       

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = '__all__'

class JobPostSerializer(serializers.ModelSerializer):
    required_skills = SkillSerializer(many=True)

    class Meta:
        model = JobPost
        fields = '__all__'
    def create(self, validated_data):
        skills_data = validated_data.pop('required_skills', [])
        job_post = JobPost.objects.create(**validated_data)
        for skill_data in skills_data:
            skill, _ = Skill.objects.get_or_create(**skill_data)
            job_post.required_skills.add(skill)
        return job_post

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('required_skills', [])
        # update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if skills_data:
            instance.required_skills.clear()
            for skill_data in skills_data:
                skill, _ = Skill.objects.get_or_create(**skill_data)
                instance.required_skills.add(skill)
        return instance

class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'