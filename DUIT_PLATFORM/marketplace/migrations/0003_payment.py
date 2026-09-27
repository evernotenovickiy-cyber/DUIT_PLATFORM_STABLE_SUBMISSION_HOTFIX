from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("marketplace", "0002_order_schedule")]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма, ₽")),
                ("method", models.CharField(choices=[("card", "Банковская карта"), ("after_service", "После выполнения")], default="after_service", max_length=24, verbose_name="Способ оплаты")),
                ("status", models.CharField(choices=[("pending", "Ожидает оплаты"), ("paid", "Оплачено"), ("failed", "Не прошла"), ("refunded", "Возвращено")], default="pending", max_length=16, verbose_name="Статус оплаты")),
                ("transaction_id", models.CharField(blank=True, max_length=40, verbose_name="ID операции")),
                ("card_last4", models.CharField(blank=True, max_length=4, verbose_name="Последние 4 цифры")),
                ("failure_reason", models.CharField(blank=True, max_length=160, verbose_name="Причина отказа")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлена")),
                ("paid_at", models.DateTimeField(blank=True, null=True, verbose_name="Оплачено")),
                ("refunded_at", models.DateTimeField(blank=True, null=True, verbose_name="Возвращено")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="marketplace.order", verbose_name="Заказ")),
            ],
            options={"verbose_name": "Платёж", "verbose_name_plural": "Платежи", "ordering": ["-created_at"]},
        ),
    ]
