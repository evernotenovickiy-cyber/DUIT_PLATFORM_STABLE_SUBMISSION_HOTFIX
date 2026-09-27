from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path

from listings.models import Service
from listings.catalog_data import CATEGORY_GROUPS, GROUP_COVERS, GROUP_FALLBACK_COVERS, RUSSIA_CITIES
from listings.management.commands.seed_demo import (
    FEMALE_FIRST, MALE_FIRST, CATEGORY_PHOTO_IDS,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Аудит финальной кураторской фото-схемы DUIT."

    def handle(self, *args, **options):
        errors = []
        catalog_categories = [name for group in CATEGORY_GROUPS for name, _ in group["items"]]
        expected_services = len(catalog_categories) * len(RUSSIA_CITIES)

        if set(catalog_categories) != set(CATEGORY_PHOTO_IDS):
            errors.append("Каталог и кураторские фотопулы не совпадают")
        weak = [name for name in catalog_categories if len(CATEGORY_PHOTO_IDS.get(name, [])) < len(RUSSIA_CITIES)]
        if weak:
            errors.append(f"Недостаточно уникальных фото для городов: {weak}")

        # Один и тот же исходный photo ID нельзя использовать в двух категориях.
        owner = {}
        duplicates = []
        for category, ids in CATEGORY_PHOTO_IDS.items():
            for photo_id in ids:
                if photo_id in owner:
                    duplicates.append((photo_id, owner[photo_id], category))
                owner[photo_id] = category
        if duplicates:
            errors.append(f"Photo ID повторяются между категориями: {duplicates[:5]}")

        providers = list(User.objects.filter(username__startswith="demo_provider_").select_related("profile").order_by("id"))
        services = list(Service.objects.filter(provider__username__startswith="demo_provider_").select_related("category", "provider").order_by("id"))

        if len(providers) != expected_services:
            errors.append(f"Ожидалось {expected_services} демо-исполнителей, найдено {len(providers)}")
        if len(services) != expected_services:
            errors.append(f"Ожидалось {expected_services} демо-услуг, найдено {len(services)}")

        avatars = [p.profile.demo_avatar_url for p in providers]
        if any(not url for url in avatars):
            errors.append("У части исполнителей отсутствует аватар")
        if len(set(avatars)) != len(avatars):
            errors.append("Аватары исполнителей повторяются")
        names = [p.get_full_name() for p in providers]
        if len(set(names)) != len(names):
            errors.append("ФИО исполнителей повторяются")
        for provider in providers:
            first = provider.first_name
            url = provider.profile.demo_avatar_url or ""
            is_female_avatar = ("/portraits/women/" in url) or ("/avatars/women_" in url)
            is_male_avatar = ("/portraits/men/" in url) or ("/avatars/men_" in url)
            if first in FEMALE_FIRST and not is_female_avatar:
                errors.append(f"Женское имя с неверным аватаром: {provider.get_full_name()}")
            if first in MALE_FIRST and not is_male_avatar:
                errors.append(f"Мужское имя с неверным аватаром: {provider.get_full_name()}")
            if url.startswith("/static/"):
                local_avatar = Path(settings.BASE_DIR) / "static" / url.removeprefix("/static/")
                if not local_avatar.exists():
                    errors.append(f"Локальный аватар отсутствует: {url}")

        used_ids = set()
        market_keys = set()
        for service in services:
            category = service.category.name if service.category else ""
            if category not in CATEGORY_PHOTO_IDS:
                errors.append(f"Неизвестная категория у услуги #{service.pk}: {category}")
                continue
            url = service.demo_image_url or ""
            prefix = "/static/demo/services/"
            if not url.startswith(prefix) or not url.endswith(".jpg"):
                errors.append(f"Услуга #{service.pk} не использует локальное demo-фото")
                continue
            try:
                photo_id = int(url.rsplit("/", 1)[1].split(".", 1)[0])
            except (ValueError, IndexError):
                errors.append(f"Нельзя прочитать photo ID у услуги #{service.pk}")
                continue
            local_photo = Path(settings.BASE_DIR) / "static" / url.removeprefix("/static/")
            if not local_photo.exists() or local_photo.stat().st_size < 25000:
                errors.append(f"Локальное фото отсутствует/повреждено: {url}")
            if photo_id not in CATEGORY_PHOTO_IDS[category]:
                errors.append(f"Фото {photo_id} не принадлежит категории «{category}»")
            if photo_id in used_ids:
                errors.append(f"Повтор исходной фотографии Pexels ID {photo_id}")
            used_ids.add(photo_id)
            key = (service.city, category)
            if key in market_keys:
                errors.append(f"Больше одной демо-услуги на пару город/категория: {key}")
            market_keys.add(key)

        group_slugs = {group["slug"] for group in CATEGORY_GROUPS}
        if set(GROUP_COVERS) != group_slugs:
            errors.append("Не для всех сфер задана cover-фотография")
        if set(GROUP_FALLBACK_COVERS) != group_slugs:
            errors.append("Не для всех сфер задан fallback")

        if errors:
            for error in errors[:30]:
                self.stderr.write(self.style.ERROR(f"MEDIA AUDIT: {error}"))
            raise CommandError(f"DUIT media audit failed: {len(errors)} issue(s)")

        self.stdout.write(self.style.SUCCESS("DUIT media audit PASSED — curated fixed-photo catalog"))
        self.stdout.write(f"Направления: {len(catalog_categories)}")
        self.stdout.write(f"Города: {len(RUSSIA_CITIES)}")
        self.stdout.write(f"Исполнители: {len(providers)} / уникальных аватаров: {len(set(avatars))}")
        self.stdout.write(f"Услуги: {len(services)} / уникальных исходных фото: {len(used_ids)} / повторов: 0")
        self.stdout.write("Service photos: LOCAL. Demo avatars: fixed live URLs with local SVG fallback.")
