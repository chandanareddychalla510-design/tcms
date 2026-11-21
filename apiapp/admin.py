from django.contrib import admin
from .models import UserProfile, AgentProfile


admin.site.register(UserProfile)
admin.site.register(AgentProfile)