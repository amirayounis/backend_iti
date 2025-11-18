from rest_framework import serializers
from .models import FreelancerPortfolio, PortfolioImage, Skill, FreelancerProfile, ClientProfile, JobPost, Proposalai

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
        model = Proposalai
        fields = '__all__'
class PortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImage
        fields = ['id', 'image']


class FreelancerPortfolioSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    user = serializers.IntegerField(source='user.user.id', read_only=True)

    class Meta:
        model = FreelancerPortfolio
        fields = [
            'id', 'user', 'name', 'project_link', 'description',
            'created_at', 'images'
        ]
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['images'] = PortfolioImageSerializer(instance.images.all(), many=True, context=self.context).data
        return representation

    def create(self, validated_data):
        uploaded_images = validated_data.pop('images', [])
        print(f"Creating portfolio with {len(uploaded_images)} images")
        portfolio = FreelancerPortfolio.objects.create(**validated_data)

        for image in uploaded_images:
            print(f"Saving image: {image}")
            PortfolioImage.objects.create(portfolio=portfolio, image=image)

        return portfolio

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('images', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for image in uploaded_images:
            PortfolioImage.objects.create(portfolio=instance, image=image)

        return instance