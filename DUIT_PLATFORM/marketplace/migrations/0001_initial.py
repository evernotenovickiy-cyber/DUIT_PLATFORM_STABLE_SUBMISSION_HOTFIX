from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="customer_conversations", to=settings.AUTH_USER_MODEL)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="provider_conversations", to=settings.AUTH_USER_MODEL)),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="conversations", to="listings.service")),
            ],
            options={"verbose_name": "Диалог", "verbose_name_plural": "Диалоги", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Favorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="listings.service")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Избранное", "verbose_name_plural": "Избранное", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена на момент заказа, ₽")),
                ("note", models.TextField(blank=True, verbose_name="Комментарий к заказу")),
                ("status", models.CharField(choices=[("new", "Новый"), ("accepted", "Принят"), ("in_progress", "В работе"), ("completed", "Завершён"), ("cancelled", "Отменён")], default="new", max_length=20, verbose_name="Статус")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="customer_orders", to=settings.AUTH_USER_MODEL, verbose_name="Заказчик")),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="provider_orders", to=settings.AUTH_USER_MODEL, verbose_name="Исполнитель")),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="listings.service", verbose_name="Услуга")),
            ],
            options={"verbose_name": "Заказ", "verbose_name_plural": "Заказы", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(max_length=3000, verbose_name="Сообщение")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_read", models.BooleanField(default=False)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="marketplace.conversation")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Сообщение", "verbose_name_plural": "Сообщения", "ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="favorite",
            constraint=models.UniqueConstraint(fields=("user", "service"), name="uniq_favorite_user_service"),
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(fields=("customer", "provider", "service"), name="uniq_conversation_participants_service"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["status", "-created_at"], name="marketplace__status_2e50fb_idx"),
        ),
    ]
