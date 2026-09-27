from django.conf import settings
from django.db import models


class Review(models.Model):
    """Отзыв заказчика об услуге исполнителя. Один отзыв на пользователя."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    service = models.ForeignKey(
        "listings.Service", on_delete=models.CASCADE, related_name="reviews", verbose_name="Услуга"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written",
        verbose_name="Автор",
    )
    rating = models.PositiveSmallIntegerField("Оценка", choices=RATING_CHOICES)
    text = models.TextField("Текст отзыва")
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]
        unique_together = ("service", "author")

    def __str__(self):
        return f"Отзыв {self.author} на «{self.service}» ({self.rating}/5)"
