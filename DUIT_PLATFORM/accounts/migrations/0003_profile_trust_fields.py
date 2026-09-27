from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("accounts","0002_profile_premium_fields")]
    operations=[
        migrations.AddField(model_name="profile", name="identity_verified", field=models.BooleanField(default=False, verbose_name="Личность подтверждена")),
        migrations.AddField(model_name="profile", name="phone_verified", field=models.BooleanField(default=False, verbose_name="Телефон подтверждён")),
        migrations.AddField(model_name="profile", name="response_time_minutes", field=models.PositiveIntegerField(default=60, verbose_name="Среднее время ответа, минут")),
        migrations.AddField(model_name="profile", name="completed_orders", field=models.PositiveIntegerField(default=0, verbose_name="Выполнено заказов")),
        migrations.AddField(model_name="profile", name="cover_url", field=models.URLField(blank=True, verbose_name="Обложка профиля")),
    ]
