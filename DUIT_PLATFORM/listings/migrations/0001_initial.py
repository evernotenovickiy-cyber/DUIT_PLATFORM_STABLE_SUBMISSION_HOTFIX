from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="Название")),
                (
                    "slug",
                    models.SlugField(blank=True, max_length=90, unique=True, verbose_name="Слаг"),
                ),
                (
                    "icon",
                    models.CharField(
                        default="🛠",
                        help_text="Один эмодзи для быстрой визуальной метки категории",
                        max_length=8,
                        verbose_name="Иконка (emoji)",
                    ),
                ),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=120, verbose_name="Название услуги")),
                (
                    "slug",
                    models.SlugField(blank=True, max_length=140, unique=True, verbose_name="Слаг"),
                ),
                ("description", models.TextField(verbose_name="Описание")),
                (
                    "price",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена, ₽"),
                ),
                ("city", models.CharField(blank=True, max_length=80, verbose_name="Город")),
                ("demo_image_url", models.URLField(blank=True, verbose_name="Демо-обложка")),
                ("is_active", models.BooleanField(default=True, verbose_name="Опубликовано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="services",
                        to="listings.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="services",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Исполнитель",
                    ),
                ),
            ],
            options={
                "verbose_name": "Услуга",
                "verbose_name_plural": "Услуги",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["-created_at"],
                        name="listings_se_created_3846d6_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ServicePhoto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(upload_to="services/%Y/%m/", verbose_name="Фото"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="listings.service",
                        verbose_name="Услуга",
                    ),
                ),
            ],
            options={
                "verbose_name": "Фото услуги",
                "verbose_name_plural": "Фото услуг",
                "ordering": ["created_at"],
            },
        ),
    ]
