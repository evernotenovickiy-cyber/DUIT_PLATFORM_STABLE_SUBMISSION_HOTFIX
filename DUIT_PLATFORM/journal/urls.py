from django.urls import path
from . import views

app_name = "journal"
urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.create, name="create"),
    path("<str:slug>/", views.detail, name="detail"),
]
