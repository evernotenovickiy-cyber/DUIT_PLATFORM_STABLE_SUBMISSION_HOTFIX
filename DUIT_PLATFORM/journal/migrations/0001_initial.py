from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="Заголовок")),
                ("slug", models.SlugField(blank=True, max_length=180, unique=True, verbose_name="Слаг")),
                ("excerpt", models.CharField(max_length=260, verbose_name="Короткое описание")),
                ("body", models.TextField(verbose_name="Текст")),
                ("kind", models.CharField(choices=[("guide", "Совет"), ("story", "История"), ("local", "Город"), ("news", "Новость")], default="guide", max_length=20, verbose_name="Тип")),
                ("city", models.CharField(blank=True, max_length=80, verbose_name="Город")),
                ("image_url", models.URLField(blank=True, verbose_name="Обложка")),
                ("is_published", models.BooleanField(default=True, verbose_name="Опубликовано")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="journal_posts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Публикация", "verbose_name_plural": "Публикации", "ordering": ["-created_at"]},
        )
    ]
