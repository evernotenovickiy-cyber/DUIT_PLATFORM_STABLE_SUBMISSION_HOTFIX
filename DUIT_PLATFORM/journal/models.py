from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Post(models.Model):
    class Kind(models.TextChoices):
        GUIDE = "guide", "Совет"
        STORY = "story", "История"
        LOCAL = "local", "Город"
        NEWS = "news", "Новость"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal_posts")
    title = models.CharField("Заголовок", max_length=160)
    slug = models.SlugField("Слаг", max_length=180, unique=True, blank=True)
    excerpt = models.CharField("Короткое описание", max_length=260)
    body = models.TextField("Текст")
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.GUIDE)
    city = models.CharField("Город", max_length=80, blank=True)
    image_url = models.URLField("Обложка", blank=True)
    is_published = models.BooleanField("Опубликовано", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "post"
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("journal:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title
