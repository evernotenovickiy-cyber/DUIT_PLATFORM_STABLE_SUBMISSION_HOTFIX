from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "city", "author", "is_published", "created_at")
    list_filter = ("kind", "city", "is_published")
    search_fields = ("title", "excerpt", "body", "author__username")
