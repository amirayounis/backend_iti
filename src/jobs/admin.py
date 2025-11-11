from django.contrib import admin
from .models import Skill, FreelancerProfile, ClientProfile, JobPost, Proposal

admin.site.register(Skill)
admin.site.register(FreelancerProfile)
admin.site.register(ClientProfile)
admin.site.register(JobPost)
admin.site.register(Proposal)