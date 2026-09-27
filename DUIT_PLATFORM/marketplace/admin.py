from django.contrib import admin

from .models import Conversation, Favorite, Message, Order, Payment


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "created_at")
    search_fields = ("user__username", "service__title")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "customer", "provider", "price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("service__title", "customer__username", "provider__username")


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "text", "created_at", "is_read")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider", "service", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at", "is_read")
    list_filter = ("is_read", "created_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "method", "status", "transaction_id", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("order__id", "transaction_id", "order__customer__username", "order__provider__username")
    readonly_fields = ("transaction_id", "card_last4", "paid_at", "refunded_at", "created_at", "updated_at")
