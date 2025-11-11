from django.db import models
from django.conf import settings

from users.models import User

class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class FreelancerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    skills = models.ManyToManyField(Skill, blank=True)
    experience_years = models.PositiveIntegerField(default=0 )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2 , null=True, blank=True)
    portfolio_website = models.URLField(blank=True)
    preferred_location = models.CharField(max_length=100, blank=True)
    job_type_preferences = models.CharField(max_length=100, blank=True, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
    ])
    linked_in_profile= models.URLField(blank=True)
    github_profile= models.URLField(blank=True)
    categories_of_expertise = models.CharField(max_length=200, blank=True ,choices=[
        ('web_development', 'Web Development'), 
        ('graphic_design', 'Graphic Design'),
        ('content_writing', 'Content Writing'),
        ('digital_marketing', 'Digital Marketing'),
        ('data_analysis', 'Data Analysis'),
        ('customer_service', 'Customer Service'),
        ('other', 'Other')
    ])
    cv = models.URLField(blank=True)
    def __str__(self):
        return f"{self.user.email}'s Profile"

class ClientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    company_description = models.TextField()
    industry = models.CharField(max_length=100)

    def __str__(self):
        return self.company_name

class JobPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)  # Full-time, Part-time, Contract, etc.
    experience_level = models.CharField(max_length=50)  # Entry, Intermediate, Expert
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_generated_criteria = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title

class Proposal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    cover_letter = models.TextField()
    proposed_budget = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    ai_suggestion_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('job', 'freelancer')

    def __str__(self):
        return f"Proposal for {self.job.title} by {self.freelancer.user.email}"