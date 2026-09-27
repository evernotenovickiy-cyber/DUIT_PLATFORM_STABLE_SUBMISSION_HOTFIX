from django.contrib import admin

from .models import Category, Service, ServicePhoto


class ServicePhotoInline(admin.TabularInline):
    model = ServicePhoto
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "provider", "category", "price", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("title", "description", "provider__username")
    inlines = [ServicePhotoInline]
