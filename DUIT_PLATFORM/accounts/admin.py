from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "city", "headline", "identity_verified", "phone_verified")
    list_filter = ("role", "identity_verified", "phone_verified", "city")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "city", "headline")
