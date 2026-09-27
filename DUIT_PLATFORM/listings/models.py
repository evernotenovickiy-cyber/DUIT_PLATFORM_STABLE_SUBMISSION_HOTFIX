from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Category(models.Model):
    """Категория услуг: кондитеры, репетиторы, ремонт и т.д."""

    name = models.CharField("Название", max_length=80, unique=True)
    slug = models.SlugField("Слаг", max_length=90, unique=True, blank=True)
    icon = models.CharField(
        "Иконка (emoji)",
        max_length=8,
        default="🛠",
        help_text="Один эмодзи для быстрой визуальной метки категории",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("listings:catalog") + f"?category={self.slug}"


class ActiveServiceManager(models.Manager):
    """Менеджер, который отдаёт только опубликованные услуги."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Service(models.Model):
    """Объявление об услуге, которое размещает исполнитель."""

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Исполнитель",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="services",
        null=True,
        blank=True,
        verbose_name="Категория",
    )
    title = models.CharField("Название услуги", max_length=120)
    slug = models.SlugField("Слаг", max_length=140, unique=True, blank=True)
    description = models.TextField("Описание")
    price = models.DecimalField("Цена, ₽", max_digits=10, decimal_places=2)
    city = models.CharField("Город", max_length=80, blank=True)
    demo_image_url = models.URLField("Демо-обложка", blank=True)
    PRICING_CHOICES = [("fixed", "Фиксированная"), ("from", "От"), ("hour", "За час"), ("project", "За проект")]
    FORMAT_CHOICES = [("provider", "У специалиста"), ("visit", "С выездом"), ("online", "Онлайн"), ("flexible", "По договорённости")]
    pricing_type = models.CharField("Тип цены", max_length=20, choices=PRICING_CHOICES, default="from")
    service_format = models.CharField("Формат", max_length=20, choices=FORMAT_CHOICES, default="flexible")
    duration_minutes = models.PositiveIntegerField("Длительность, минут", default=60)
    lead_time = models.CharField("Срок / ближайшее время", max_length=120, blank=True, default="Сегодня или завтра")
    included = models.TextField("Что входит", blank=True)
    process = models.TextField("Как проходит работа", blank=True)
    availability_note = models.CharField("Доступность", max_length=160, blank=True, default="Есть свободные окна")
    completed_orders = models.PositiveIntegerField("Выполнено заказов", default=0)
    is_active = models.BooleanField("Опубликовано", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    objects = models.Manager()
    active = ActiveServiceManager()

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"], name="listings_se_created_3846d6_idx")]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or "service"
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("listings:service_detail", kwargs={"slug": self.slug})

    @property
    def average_rating(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("reviews")
        if prefetched is not None:
            if not prefetched:
                return None
            return round(sum(review.rating for review in prefetched) / len(prefetched), 1)
        result = self.reviews.aggregate(models.Avg("rating"))["rating__avg"]
        return round(result, 1) if result else None

    @property
    def reviews_count(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("reviews")
        if prefetched is not None:
            return len(prefetched)
        return self.reviews.count()

    @property
    def cover_photo(self):
        return self.photos.first()

    @property
    def cover_image_url(self):
        photo = self.cover_photo
        if photo and photo.image:
            return photo.image.url
        return self.demo_image_url or self.fallback_image_url

    @property
    def fallback_image_url(self):
        """Локальная офлайн-обложка с вариациями внутри каждой сферы."""
        from .catalog_data import group_for_category_name
        if self.category_id and self.category:
            group = group_for_category_name(self.category.name)
            if group:
                variant = ((self.pk or 1) - 1) % 4 + 1
                return f"/static/img/demo/services/{group['slug']}-{variant:02d}.svg"
        return "/static/img/demo/services/business-01.svg"


class ServicePhoto(models.Model):
    """Одна фотография из портфолио/объявления услуги."""

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="photos", verbose_name="Услуга"
    )
    image = models.ImageField("Фото", upload_to="services/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фото услуги"
        verbose_name_plural = "Фото услуг"
        ordering = ["created_at"]

    def __str__(self):
        return f"Фото для «{self.service.title}»"
