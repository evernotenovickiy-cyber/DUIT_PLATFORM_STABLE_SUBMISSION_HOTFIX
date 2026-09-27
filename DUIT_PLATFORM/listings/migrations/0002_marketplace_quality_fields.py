from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("listings","0001_initial")]
    operations=[
        migrations.AddField(model_name="service", name="pricing_type", field=models.CharField(choices=[("fixed","Фиксированная"),("from","От"),("hour","За час"),("project","За проект")], default="from", max_length=20, verbose_name="Тип цены")),
        migrations.AddField(model_name="service", name="service_format", field=models.CharField(choices=[("provider","У специалиста"),("visit","С выездом"),("online","Онлайн"),("flexible","По договорённости")], default="flexible", max_length=20, verbose_name="Формат")),
        migrations.AddField(model_name="service", name="duration_minutes", field=models.PositiveIntegerField(default=60, verbose_name="Длительность, минут")),
        migrations.AddField(model_name="service", name="lead_time", field=models.CharField(blank=True, default="Сегодня или завтра", max_length=120, verbose_name="Срок / ближайшее время")),
        migrations.AddField(model_name="service", name="included", field=models.TextField(blank=True, verbose_name="Что входит")),
        migrations.AddField(model_name="service", name="process", field=models.TextField(blank=True, verbose_name="Как проходит работа")),
        migrations.AddField(model_name="service", name="availability_note", field=models.CharField(blank=True, default="Есть свободные окна", max_length=160, verbose_name="Доступность")),
        migrations.AddField(model_name="service", name="completed_orders", field=models.PositiveIntegerField(default=0, verbose_name="Выполнено заказов")),
    ]
