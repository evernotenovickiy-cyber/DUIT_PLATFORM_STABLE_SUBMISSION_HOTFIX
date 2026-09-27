from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Профиль пользователя DUIT: заказчик, исполнитель или универсальный аккаунт."""

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Ищу услуги"
        PROVIDER = "provider", "Оказываю услуги"
        BOTH = "both", "Ищу и оказываю услуги"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField("Роль", max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True, null=True)
    bio = models.TextField("О себе", blank=True)
    headline = models.CharField("Специализация", max_length=120, blank=True)
    demo_avatar_url = models.URLField("Демо-аватар", blank=True)
    experience_years = models.PositiveSmallIntegerField("Лет опыта", default=0)
    is_verified = models.BooleanField("Профиль подтверждён", default=False)
    identity_verified = models.BooleanField("Личность подтверждена", default=False)
    phone_verified = models.BooleanField("Телефон подтверждён", default=False)
    response_time_minutes = models.PositiveIntegerField("Среднее время ответа, минут", default=60)
    completed_orders = models.PositiveIntegerField("Выполнено заказов", default=0)
    cover_url = models.URLField("Обложка профиля", blank=True)
    city = models.CharField("Город", max_length=80, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    telegram = models.CharField("Telegram", max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return self.demo_avatar_url or self.fallback_avatar_url

    @property
    def fallback_avatar_url(self):
        index = ((self.user_id or 1) - 1) % 48 + 1
        return f"/static/img/demo/avatars/avatar-{index:02d}.svg"

    @property
    def can_sell(self):
        return self.role in {self.Role.PROVIDER, self.Role.BOTH}

    @property
    def can_buy(self):
        return self.role in {self.Role.CUSTOMER, self.Role.BOTH}

    def __str__(self):
        return f"Профиль {self.user.username}"
