"""Кураторский каталог DUIT.

Финальная демо-сборка намеренно использует ограниченный набор услуг,
для которых подобраны фиксированные проверенные фото. Это лучше, чем сотни
направлений со случайными или семантически неверными изображениями.
"""

CATEGORY_GROUPS = [
    {"slug":"beauty","title":"Красота","icon":"✨","items":[
        ("Маникюр и педикюр","💅"),("Барберы","🧔"),("Макияж","💄"),
    ]},
    {"slug":"health","title":"Здоровье и wellness","icon":"💚","items":[
        ("Массаж","💆"),
    ]},
    {"slug":"home","title":"Дом и ремонт","icon":"🏠","items":[
        ("Сантехника","🚿"),("Электрика","💡"),
    ]},
    {"slug":"cleaning","title":"Уборка","icon":"🫧","items":[
        ("Уборка квартир","🧹"),
    ]},
    {"slug":"pets","title":"Животные","icon":"🐾","items":[
        ("Груминг","🐕"),
    ]},
    {"slug":"education","title":"Обучение","icon":"🎓","items":[
        ("Репетиторы","📚"),
    ]},
    {"slug":"photo-video","title":"Фото и видео","icon":"📷","items":[
        ("Фотографы","📸"),
    ]},
    {"slug":"food","title":"Еда и десерты","icon":"🍰","items":[
        ("Кондитеры","🎂"),
    ]},
    {"slug":"delivery","title":"Доставка","icon":"🚚","items":[
        ("Курьеры","📦"),
    ]},
    {"slug":"auto","title":"Авто","icon":"🚗","items":[
        ("Ремонт автомобилей","🔧"),
    ]},
    {"slug":"sport","title":"Спорт и движение","icon":"🧘","items":[
        ("Йога","🧘"),
    ]},
    {"slug":"care","title":"Помощь и забота","icon":"🤝","items":[
        ("Няни","🧸"),
    ]},
]

# Четыре города дают по одной уникальной карточке на каждое направление.
# Итого 60 услуг = 60 разных проверенных фото.
RUSSIA_CITIES = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург"]


def _pexels(photo_id):
    # Используем тот же локальный кадр, который входит в offline-пакет.
    return f"/static/demo/services/{photo_id}.jpg"


# Обложки сфер тоже фиксированные, без случайной выдачи.
GROUP_COVERS = {
    "beauty": _pexels(34930163),
    "health": _pexels(7235061),
    "home": _pexels(32588548),
    "cleaning": _pexels(7513086),
    "pets": _pexels(19145886),
    "education": _pexels(5311450),
    "photo-video": _pexels(33665110),
    "food": _pexels(36993349),
    "delivery": _pexels(13431965),
    "auto": _pexels(8478243),
    "sport": _pexels(29957507),
    "care": _pexels(8954876),
}

GROUP_FALLBACK_COVERS = {slug: f"/static/img/categories/{slug}.svg" for slug in GROUP_COVERS}

POPULAR_SEARCHES = [
    "маникюр", "барбер", "массаж", "сантехник", "электрик",
    "уборка", "груминг", "репетитор", "фотограф", "торт на заказ",
]


def all_category_pairs():
    for group in CATEGORY_GROUPS:
        for name, icon in group["items"]:
            yield name, icon


def names_for_group(slug):
    for group in CATEGORY_GROUPS:
        if group["slug"] == slug:
            return [name for name, _ in group["items"]]
    return []


def group_for_category_name(name):
    for group in CATEGORY_GROUPS:
        if any(item_name == name for item_name, _ in group["items"]):
            return group
    return None


def build_group_context(categories):
    by_name = {category.name: category for category in categories}
    result = []
    for source in CATEGORY_GROUPS:
        items = [by_name[name] for name, _ in source["items"] if name in by_name]
        result.append({
            "slug": source["slug"],
            "title": source["title"],
            "icon": source["icon"],
            "items": items,
            "preview": items[:4],
            "services_count": sum(getattr(item, "active_count", 0) or 0 for item in items),
            "cover_url": GROUP_COVERS.get(source["slug"], ""),
            "fallback_cover_url": GROUP_FALLBACK_COVERS.get(source["slug"], "/static/img/categories/business.svg"),
        })
    return result
