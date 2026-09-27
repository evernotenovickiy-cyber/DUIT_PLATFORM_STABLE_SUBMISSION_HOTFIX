from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<str:slug>/", views.service_detail, name="service_detail"),
    path("services/<str:slug>/edit/", views.service_edit, name="service_edit"),
    path("services/<str:slug>/delete/", views.service_delete, name="service_delete"),
    path("photos/<int:photo_id>/delete/", views.service_photo_delete, name="service_photo_delete"),
    path("u/<str:username>/", views.provider_detail, name="provider_detail"),
]
