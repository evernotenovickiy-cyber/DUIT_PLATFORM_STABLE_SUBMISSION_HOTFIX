from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("favorites/", views.favorites, name="favorites"),
    path("favorites/toggle/<int:service_id>/", views.favorite_toggle, name="favorite_toggle"),
    path("orders/new/<int:service_id>/", views.order_create, name="order_create"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<int:order_id>/payment/", views.payment_checkout, name="payment_checkout"),
    path("orders/<int:order_id>/payment/success/", views.payment_success, name="payment_success"),
    path("orders/<int:order_id>/status/<str:status>/", views.order_status, name="order_status"),
    path("messages/", views.inbox, name="inbox"),
    path("messages/start/<int:service_id>/", views.conversation_start, name="conversation_start"),
    path("messages/<int:conversation_id>/", views.conversation, name="conversation"),
    path("messages/<int:conversation_id>/json/", views.conversation_messages_json, name="conversation_json"),
]
