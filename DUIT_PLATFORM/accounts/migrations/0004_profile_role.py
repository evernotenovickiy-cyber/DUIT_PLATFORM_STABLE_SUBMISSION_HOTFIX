from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_profile_trust_fields")]
    operations = [
        migrations.AddField(
            model_name="profile",
            name="role",
            field=models.CharField(
                choices=[
                    ("customer", "Ищу услуги"),
                    ("provider", "Оказываю услуги"),
                    ("both", "Ищу и оказываю услуги"),
                ],
                default="customer",
                max_length=20,
                verbose_name="Роль",
            ),
        ),
    ]
