from .models import Category


def categories_processor(request):
    """Делает список категорий доступным во всех шаблонах (для меню/фильтров)."""
    return {"nav_categories": Category.objects.all()}
