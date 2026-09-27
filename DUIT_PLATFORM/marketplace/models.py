from django.conf import settings
from django.db import models

from listings.models import Service


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "service"], name="uniq_favorite_user_service")
        ]
        ordering = ["-created_at"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user} → {self.service}"


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        ACCEPTED = "accepted", "Принят"
        IN_PROGRESS = "in_progress", "В работе"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_orders", verbose_name="Заказчик")
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_orders", verbose_name="Исполнитель")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="orders", verbose_name="Услуга")
    price = models.DecimalField("Цена на момент заказа, ₽", max_digits=10, decimal_places=2)
    note = models.TextField("Комментарий к заказу", blank=True)
    desired_date = models.DateField("Желаемая дата", null=True, blank=True)
    desired_time = models.TimeField("Желаемое время", null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        indexes = [models.Index(fields=["status", "-created_at"], name="marketplace__status_2e50fb_idx")]

    def __str__(self):
        return f"Заказ #{self.pk}: {self.service.title}"

    def can_view(self, user):
        return user.is_authenticated and user in (self.customer, self.provider)


class Payment(models.Model):
    class Method(models.TextChoices):
        CARD = "card", "Банковская карта"
        AFTER_SERVICE = "after_service", "После выполнения"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачено"
        FAILED = "failed", "Не прошла"
        REFUNDED = "refunded", "Возвращено"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment", verbose_name="Заказ")
    amount = models.DecimalField("Сумма, ₽", max_digits=10, decimal_places=2)
    method = models.CharField("Способ оплаты", max_length=24, choices=Method.choices, default=Method.AFTER_SERVICE)
    status = models.CharField("Статус оплаты", max_length=16, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField("ID операции", max_length=40, blank=True)
    card_last4 = models.CharField("Последние 4 цифры", max_length=4, blank=True)
    failure_reason = models.CharField("Причина отказа", max_length=160, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)
    paid_at = models.DateTimeField("Оплачено", null=True, blank=True)
    refunded_at = models.DateTimeField("Возвращено", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"Платёж заказа #{self.order_id}: {self.get_status_display()}"


class Conversation(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_conversations")
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_conversations")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["customer", "provider", "service"], name="uniq_conversation_participants_service")
        ]
        verbose_name = "Диалог"
        verbose_name_plural = "Диалоги"

    def __str__(self):
        return f"Диалог {self.customer} ↔ {self.provider}"

    def other_user(self, user):
        return self.provider if user == self.customer else self.customer


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    text = models.TextField("Сообщение", max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return f"{self.sender}: {self.text[:40]}"
