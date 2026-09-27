from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(model_name="profile", name="headline", field=models.CharField(blank=True, max_length=120, verbose_name="Специализация")),
        migrations.AddField(model_name="profile", name="demo_avatar_url", field=models.URLField(blank=True, verbose_name="Демо-аватар")),
        migrations.AddField(model_name="profile", name="experience_years", field=models.PositiveSmallIntegerField(default=0, verbose_name="Лет опыта")),
        migrations.AddField(model_name="profile", name="is_verified", field=models.BooleanField(default=False, verbose_name="Профиль подтверждён")),
    ]
