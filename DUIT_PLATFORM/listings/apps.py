from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "listings"
    verbose_name = "Услуги"

    def ready(self):
        from . import signals  # noqa: F401
