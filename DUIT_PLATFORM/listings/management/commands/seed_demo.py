from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from journal.models import Post
from listings.catalog_data import CATEGORY_GROUPS, RUSSIA_CITIES, all_category_pairs, group_for_category_name
from listings.models import Category, Service
from marketplace.models import Conversation, Favorite, Message, Order, Payment
from reviews.models import Review

User = get_user_model()

FEMALE_FIRST = ["Анна","София","Мария","Елена","Полина","Дарья","Ксения","Алина","Виктория","Юлия","Ольга","Светлана","Вера","Евгения","Надежда","Татьяна","Валерия","Диана","Анастасия","Екатерина","Ирина","Наталья","Марина","Александра","Людмила","Кристина","Вероника"]
MALE_FIRST = ["Михаил","Алексей","Илья","Даниил","Максим","Артём","Никита","Роман","Андрей","Сергей","Дмитрий","Павел","Матвей","Кирилл","Игорь","Лев","Арсений","Георгий","Александр","Владимир","Антон","Денис","Олег","Вадим","Константин","Егор","Виктор"]
FEMALE_LAST = ["Соколова","Лебедева","Волкова","Попова","Васильева","Новикова","Михайлова","Павлова","Степанова","Захарова","Кузьмина","Макарова","Громова","Тихонова","Филиппова","Крылова","Котова","Жукова","Иванова","Сергеева","Алексеева","Титова","Ковалёва","Белова","Морозова","Орлова","Фролова","Наумова","Дорофеева","Баранова","Миронова"]
MALE_LAST = ["Орлов","Морозов","Кузнецов","Смирнов","Петров","Фёдоров","Семёнов","Козлов","Николаев","Белов","Поляков","Егоров","Виноградов","Комаров","Савельев","Мельников","Давыдов","Тарасов","Иванов","Сергеев","Алексеев","Титов","Ковалёв","Фролов","Наумов","Дорофеев","Баранов","Миронов","Гусев","Королёв","Рябов"]

# Финальная политика фото: только фиксированные Pexels photo IDs, вручную
# проверенные на соответствие услуге. Никаких LoremFlickr, random search,
# соседних сфер и подмены по ключевым словам.
CATEGORY_PHOTO_IDS = {
    "Маникюр и педикюр": [34930163, 34930151, 34930165, 34930100],
    "Барберы": [4952625, 7518710, 7518732, 3998397],
    "Макияж": [33580449, 20592897, 33607403, 11041338],
    "Массаж": [7235061, 5793784, 9336026, 11982069],
    "Сантехника": [32588548, 16509869, 37340086, 32497162],
    "Электрика": [38760190, 21812143, 21357685, 33694019],
    "Уборка квартир": [7513086, 7513011, 27176671, 6197053],
    "Груминг": [19145886, 6816844, 6816863, 6816837],
    "Репетиторы": [5311450, 5311406, 5905712, 6929182],
    "Фотографы": [33665110, 34970546, 20230572, 18386861],
    "Кондитеры": [36993349, 5953870, 37105711, 3983575],
    "Курьеры": [13431965, 6699414, 6407560, 12725400],
    "Ремонт автомобилей": [8478243, 4116231, 8478248, 33814735],
    "Йога": [29957507, 8436426, 13087350, 3822689],
    "Няни": [8954876, 6974748, 8954871, 6974310],
}
# Обратная совместимость для тестов/аудита старой версии имени константы.
CATEGORY_PHOTO_QUERIES = CATEGORY_PHOTO_IDS

GROUP_PRICE = {
    "beauty": 2200, "health": 2800, "home": 2500, "cleaning": 3200,
    "pets": 2000, "education": 1700, "photo-video": 5500, "food": 4200,
    "delivery": 1200, "auto": 4000, "sport": 1800, "care": 1600,
}

CATEGORY_TITLES = {
    "Маникюр и педикюр": ["Маникюр с покрытием и дизайном", "Аппаратный маникюр", "Нюдовый маникюр и укрепление", "Маникюр и педикюр по записи"],
    "Барберы": ["Стрижка и уход за бородой", "Мужская стрижка и борода", "Fade и оформление бороды", "Классическая стрижка в барбершопе"],
    "Макияж": ["Макияж на мероприятие", "Вечерний макияж", "Макияж для фотосессии", "Индивидуальный образ с визажистом"],
    "Массаж": ["Расслабляющий массаж 60 минут", "Массаж спины и шеи", "Спортивный массаж", "Восстановительный массаж"],
    "Сантехника": ["Сантехник: кран, смеситель, трубы", "Ремонт сантехники на дому", "Устранение протечек", "Монтаж и ремонт сантехники"],
    "Электрика": ["Электрик на дом", "Диагностика и ремонт электрики", "Монтаж розеток и освещения", "Электромонтажные работы"],
    "Уборка квартир": ["Уборка квартиры", "Поддерживающая уборка", "Клининг квартиры", "Уборка перед гостями"],
    "Груминг": ["Груминг собак", "Стрижка и уход за питомцем", "Комплексный груминг", "Груминг маленьких пород"],
    "Репетиторы": ["Репетитор: индивидуальные занятия", "Помощь с учёбой", "Подготовка к экзаменам", "Персональные занятия с преподавателем"],
    "Фотографы": ["Портретная фотосессия", "Семейная фотосессия", "Фотограф на событие", "Студийная фотосессия"],
    "Кондитеры": ["Торт на заказ", "Авторский праздничный торт", "Торт по вашему эскизу", "Торт с индивидуальным декором"],
    "Курьеры": ["Курьерская доставка", "Доставка документов и посылок", "Курьер по городу", "Срочная доставка"],
    "Ремонт автомобилей": ["Ремонт автомобиля", "Диагностика и ремонт авто", "Ремонт двигателя и ходовой", "Автомеханик по записи"],
    "Йога": ["Персональная йога", "Йога для начинающих", "Йога для спины", "Индивидуальная практика йоги"],
    "Няни": ["Няня на несколько часов", "Няня для ребёнка", "Помощь с ребёнком дома", "Бэбиситтер по записи"],
}

CATEGORY_HEADLINES = {
    "Маникюр и педикюр":"Мастер маникюра", "Барберы":"Барбер", "Макияж":"Визажист",
    "Массаж":"Массажист", "Сантехника":"Сантехник", "Электрика":"Электрик",
    "Уборка квартир":"Клинер", "Груминг":"Грумер", "Репетиторы":"Репетитор",
    "Фотографы":"Фотограф", "Кондитеры":"Кондитер", "Курьеры":"Курьер",
    "Ремонт автомобилей":"Автомеханик", "Йога":"Инструктор по йоге", "Няни":"Няня",
}

PROFILE_BIOS = [
    "Работаю по записи и заранее фиксирую стоимость. В чате уточняю задачу, сроки и детали — без неожиданных доплат.",
    "Для меня важны понятные договорённости, аккуратный результат и спокойная коммуникация. Всегда предупреждаю о нюансах заранее.",
    "Сначала выясняю задачу и ожидания, затем предлагаю подходящий вариант. После выполнения остаюсь на связи.",
    "Ценю время клиента: отвечаю быстро, называю цену до начала и соблюдаю договорённости.",
]
REVIEW_TEXTS = [
    "Всё обсудили заранее, результат понравился. Цена не изменилась.",
    "Очень аккуратно и профессионально. Буду обращаться ещё.",
    "Специалист приехал вовремя и всё подробно объяснил.",
    "Хороший сервис и понятные условия. Рекомендую.",
    "Удобно договорились в чате, всё прошло без сюрпризов.",
    "Качественная работа, доброжелательное общение.",
]
INCLUDED = "консультация до начала · основная работа · рекомендации после выполнения"
PROCESS = "1. Вы описываете задачу. 2. Согласуем время и цену. 3. Выполняется работа. 4. Вы принимаете результат."


def pexels(photo_id, variant=0, unique_key=None):
    # Финальная offline-сборка: изображение хранится локально в static/demo/services.
    return f"/static/demo/services/{photo_id}.jpg"


def category_photo_code(category):
    # Оставлено для совместимости с импортами; теперь кодом категории является её имя.
    return category


def photo_pool(category, group_slug=None):
    if category not in CATEGORY_PHOTO_IDS:
        raise KeyError(f"Для категории нет кураторского фотопула: {category}")
    return list(CATEGORY_PHOTO_IDS[category])


def service_photo(category, group_slug=None, city_index=0, category_index=0, variant=0, unique_key=0):
    pool = photo_pool(category)
    photo_id = pool[(city_index + variant) % len(pool)]
    return pexels(photo_id, variant=city_index, unique_key=f"{category_index}-{unique_key}")


def avatar_url(gender, gender_index):
    """Stable live demo avatar URL.

    We intentionally do not pre-download RandomUser portraits during startup: some
    networks return small anti-bot responses instead of the image. The browser can
    load the fixed portrait URL directly, while templates keep a local SVG fallback.
    The gender is encoded in the URL and audited.
    """
    folder = "women" if gender == "f" else "men"
    if not 0 <= gender_index < 100:
        raise ValueError(f"Исчерпан пул аватаров {folder}: {gender_index}")
    return f"https://randomuser.me/api/portraits/{folder}/{gender_index}.jpg"


def person_name(gender, slot):
    firsts, lasts = (FEMALE_FIRST, FEMALE_LAST) if gender == "f" else (MALE_FIRST, MALE_LAST)
    return firsts[slot % len(firsts)], lasts[(slot // len(firsts)) % len(lasts)]


class Command(BaseCommand):
    help = "Создаёт компактную кураторскую демо-среду DUIT с проверенными фотографиями."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        curated_names = [name for name, _ in all_category_pairs()]
        categories = {}
        for name, icon in all_category_pairs():
            category, _ = Category.objects.get_or_create(name=name)
            if category.icon != icon:
                category.icon = icon
                category.save(update_fields=["icon"])
            categories[name] = category

        if options.get("if_empty") and self._existing_demo_is_curated():
            self._ensure_core_accounts()
            self.stdout.write(self.style.WARNING("Кураторский демо-каталог уже готов — seed пропущен."))
            return

        self._clear_demo()
        # На чистой учебной БД убираем старые пустые демо-категории прошлых версий.
        Category.objects.exclude(name__in=curated_names).filter(services__isnull=True).delete()

        client, admin = self._ensure_core_accounts()
        reviewers = self._create_reviewers()

        services = []
        review_objects = []
        provider_counter = 0
        gender_slots = {"f": 0, "m": 0}
        avatar_slots = {"f": 0, "m": 0}
        all_photo_ids = set()

        for category_index, category_name in enumerate(curated_names):
            group = group_for_category_name(category_name)
            group_slug = group["slug"]
            base_price = GROUP_PRICE[group_slug]
            pool = CATEGORY_PHOTO_IDS[category_name]
            if len(pool) < len(RUSSIA_CITIES):
                raise RuntimeError(f"Недостаточно фото для {category_name}: {len(pool)}")

            for city_index, city in enumerate(RUSSIA_CITIES):
                gender = "f" if provider_counter % 2 == 0 else "m"
                first, last = person_name(gender, gender_slots[gender])
                gender_slots[gender] += 1
                username = f"demo_provider_{category_index:02d}_{city_index:02d}"
                provider = User.objects.create(
                    username=username,
                    email=f"{username}@duit.local",
                    first_name=first,
                    last_name=last,
                )
                if provider_counter == 0:
                    provider.set_password("duit12345")
                else:
                    provider.set_unusable_password()
                provider.save(update_fields=["password"])

                photo_id = pool[city_index]
                if photo_id in all_photo_ids:
                    raise RuntimeError(f"Фото ID {photo_id} повторно используется в демо-каталоге")
                all_photo_ids.add(photo_id)
                image_url = pexels(photo_id, variant=city_index, unique_key=f"service-{category_index}-{city_index}")

                profile = provider.profile
                profile.role = Profile.Role.PROVIDER
                profile.city = city
                profile.headline = CATEGORY_HEADLINES[category_name]
                profile.bio = PROFILE_BIOS[provider_counter % len(PROFILE_BIOS)]
                profile.experience_years = 2 + (provider_counter * 3) % 13
                profile.is_verified = True
                profile.identity_verified = provider_counter % 6 != 0
                profile.phone_verified = True
                profile.response_time_minutes = [8, 12, 18, 25, 35][provider_counter % 5]
                profile.completed_orders = 9 + (provider_counter * 11) % 140
                profile.demo_avatar_url = avatar_url(gender, avatar_slots[gender])
                avatar_slots[gender] += 1
                profile.cover_url = image_url
                profile.save()

                title = CATEGORY_TITLES[category_name][city_index % len(CATEGORY_TITLES[category_name])]
                price = base_price + city_index * 250 + (category_index % 4) * 150
                service = Service.objects.create(
                    provider=provider,
                    category=categories[category_name],
                    title=title,
                    description=(
                        f"{CATEGORY_HEADLINES[category_name]} в городе {city}. "
                        "Перед заказом уточняю задачу, удобное время и итоговую стоимость. "
                        "Все договорённости фиксируем в чате DUIT."
                    ),
                    price=price,
                    city=city,
                    demo_image_url=image_url,
                    is_active=True,
                    pricing_type=["from", "fixed", "hour", "fixed"][city_index],
                    service_format=["provider", "visit", "flexible", "provider"][city_index],
                    duration_minutes=[60, 90, 60, 120][city_index],
                    lead_time=["Сегодня после 18:00", "Есть окна завтра", "Запись на этой неделе", "Есть время на выходных"][city_index],
                    included=INCLUDED,
                    process=PROCESS,
                    availability_note=["Есть свободное время сегодня", "Свободно завтра", "Принимаю новые заказы", "Есть окна на выходных"][city_index],
                    completed_orders=15 + (provider_counter * 13) % 170,
                )
                services.append(service)

                for j in range(4):
                    reviewer = reviewers[(provider_counter * 3 + j) % len(reviewers)]
                    rating = [5, 5, 4, 5][(provider_counter + j) % 4]
                    review_objects.append(Review(
                        service=service,
                        author=reviewer,
                        rating=rating,
                        text=REVIEW_TEXTS[(provider_counter + j) % len(REVIEW_TEXTS)],
                    ))
                provider_counter += 1

        Review.objects.bulk_create(review_objects, batch_size=500, ignore_conflicts=True)
        self._create_journal(admin)

        demo_service = Service.objects.get(category__name="Кондитеры", city="Москва")
        Favorite.objects.get_or_create(user=client, service=demo_service)
        order = Order.objects.create(
            customer=client, provider=demo_service.provider, service=demo_service,
            price=demo_service.price, note="Нужен торт к семейному празднику.", status=Order.Status.ACCEPTED,
        )
        Payment.objects.create(
            order=order, amount=order.price, method=Payment.Method.CARD,
            status=Payment.Status.PAID, transaction_id="DUIT-DEMO-0001",
            card_last4="4242", paid_at=timezone.now(),
        )
        conv, _ = Conversation.objects.get_or_create(customer=client, provider=demo_service.provider, service=demo_service)
        Message.objects.create(conversation=conv, sender=client, text="Здравствуйте! Можно обсудить заказ?")
        Message.objects.create(conversation=conv, sender=demo_service.provider, text="Здравствуйте! Конечно, расскажите о пожеланиях.")

        self.stdout.write(self.style.SUCCESS(f"Категорий: {len(curated_names)}"))
        self.stdout.write(self.style.SUCCESS(f"Города: {len(RUSSIA_CITIES)}"))
        self.stdout.write(self.style.SUCCESS(f"Исполнители: {provider_counter}"))
        self.stdout.write(self.style.SUCCESS(f"Услуги: {len(services)} / живых фото: {len(all_photo_ids)} / повторов: 0"))
        self.stdout.write(self.style.SUCCESS(f"Отзывы: {len(review_objects)}"))
        self.stdout.write("Клиент: demo_client / duit12345")
        self.stdout.write("Исполнитель: demo_provider_00_00 / duit12345")
        self.stdout.write("Админ: admin / admin123")

    def _create_reviewers(self):
        reviewers = []
        for i in range(32):
            username = f"demo_reviewer_{i:03d}"
            gender = "f" if i % 2 == 0 else "m"
            first, last = person_name(gender, 300 + i)
            user = User.objects.create(username=username, email=f"{username}@duit.local", first_name=first, last_name=last)
            user.set_unusable_password()
            user.save(update_fields=["password"])
            profile = user.profile
            profile.role = Profile.Role.CUSTOMER
            profile.city = RUSSIA_CITIES[i % len(RUSSIA_CITIES)]
            profile.save()
            reviewers.append(user)
        return reviewers

    def _create_journal(self, admin):
        specs = [
            ("guide", "Как выбрать исполнителя и не переплатить", "Москва", "Пять вопросов перед заказом.", "Сравните условия, рейтинг и отзывы. До заказа уточните стоимость, сроки и что входит в работу.", 5311450),
            ("guide", "Что спросить у грумера перед первой записью", "Санкт-Петербург", "Короткий чек-лист для владельцев питомцев.", "Расскажите о породе, поведении и особенностях питомца. Уточните длительность и состав процедуры.", 6816863),
            ("story", "Как кондитер собирает портфолио", "Казань", "Почему хорошие фото помогают клиенту выбрать.", "Показывайте реальные работы, честную цену и понятные условия. Это снижает количество вопросов до заказа.", 36993349),
        ]
        for kind, title, city, excerpt, body, photo_id in specs:
            Post.objects.create(author=admin, kind=kind, title=title, city=city, excerpt=excerpt, body=body, image_url=pexels(photo_id), is_published=True)

    def _ensure_core_accounts(self):
        client, _ = User.objects.get_or_create(username="demo_client", defaults={"email": "demo_client@duit.local"})
        client.first_name, client.last_name = "Евгений", "Клиент"
        client.set_password("duit12345")
        client.save()
        cp = client.profile
        cp.role = Profile.Role.CUSTOMER
        cp.city = "Москва"
        cp.headline = "Заказчик DUIT"
        cp.save()

        admin, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@duit.local"})
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("admin123")
        admin.save()
        return client, admin

    def _existing_demo_is_curated(self):
        services = Service.objects.filter(provider__username__startswith="demo_provider_").select_related("category")
        expected = len(CATEGORY_PHOTO_IDS) * len(RUSSIA_CITIES)
        if services.count() != expected:
            return False
        used_ids = set()
        for service in services:
            category = service.category.name if service.category else ""
            if category not in CATEGORY_PHOTO_IDS:
                return False
            url = service.demo_image_url or ""
            prefix = "/static/demo/services/"
            if not url.startswith(prefix) or not url.endswith(".jpg"):
                return False
            try:
                photo_id = int(url.rsplit("/", 1)[1].split(".", 1)[0])
            except (ValueError, IndexError):
                return False
            if photo_id not in CATEGORY_PHOTO_IDS[category] or photo_id in used_ids:
                return False
            used_ids.add(photo_id)
        return len(used_ids) == expected

    def _clear_demo(self):
        demo_provider_ids = list(User.objects.filter(username__startswith="demo_provider_").values_list("id", flat=True))
        demo_reviewer_ids = list(User.objects.filter(username__startswith="demo_reviewer_").values_list("id", flat=True))
        demo_ids = demo_provider_ids + demo_reviewer_ids
        if demo_provider_ids:
            demo_services = Service.objects.filter(provider_id__in=demo_provider_ids)
            Order.objects.filter(service__in=demo_services).delete()
            Conversation.objects.filter(service__in=demo_services).delete()
            Favorite.objects.filter(service__in=demo_services).delete()
            Review.objects.filter(service__in=demo_services).delete()
            demo_services.delete()
        if demo_ids:
            Review.objects.filter(author_id__in=demo_ids).delete()
            User.objects.filter(id__in=demo_ids).delete()
        Post.objects.filter(author__username="admin").delete()
        client = User.objects.filter(username="demo_client").first()
        if client:
            Favorite.objects.filter(user=client).delete()
            Order.objects.filter(customer=client).delete()
            Conversation.objects.filter(customer=client).delete()
