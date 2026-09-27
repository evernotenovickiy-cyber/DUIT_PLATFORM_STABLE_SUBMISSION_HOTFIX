from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from reviews.forms import ReviewForm
from reviews.models import Review
from marketplace.models import Order
from journal.models import Post
from accounts.models import Profile

from .catalog_data import (
    CATEGORY_GROUPS,
    POPULAR_SEARCHES,
    RUSSIA_CITIES,
    build_group_context,
    group_for_category_name,
    names_for_group,
)
from .forms import ServiceForm, ServicePhotosForm
from .models import Category, Service, ServicePhoto

User = get_user_model()

SEARCH_SYNONYMS = {
    "ногти": ["маникюр", "педикюр"], "маник": ["маникюр"], "бровки": ["брови"],
    "кран": ["сантехника", "мастер на час"], "сантехник": ["сантехника"],
    "пёс": ["выгул собак", "груминг", "дрессировка"], "собака": ["выгул собак", "груминг"],
    "кот": ["зооняня", "передержка"], "торт": ["кондитеры", "выпечка на заказ"],
    "фотосессия": ["фотографы"], "фото": ["фотографы", "контент-съёмка"],
    "починить ноутбук": ["ремонт ноутбуков"], "сайт": ["разработка сайтов"],
    "убраться": ["уборка квартир", "генеральная уборка"], "массажист": ["массаж"],
}

def _favorite_ids(request):
    if not request.user.is_authenticated:
        return set()
    return set(request.user.favorites.values_list("service_id", flat=True))

def _card_queryset():
    return Service.active.select_related("provider", "category").prefetch_related("photos", "reviews")


def _photo_signature(service):
    url = service.demo_image_url or ""
    marker = "/photos/"
    if marker in url:
        tail = url.split(marker, 1)[1]
        return tail.split("/", 1)[0]
    return url or service.fallback_image_url


def _diverse_services(queryset, limit=8):
    """Витрина без повторов исполнителя и одного исходного фотокадра."""
    result, provider_ids, photo_ids = [], set(), set()
    candidates = list(queryset[: max(limit * 12, 80)])
    for service in candidates:
        signature = _photo_signature(service)
        if service.provider_id in provider_ids or signature in photo_ids:
            continue
        result.append(service)
        provider_ids.add(service.provider_id)
        photo_ids.add(signature)
        if len(result) >= limit:
            return result

    # Если тематический пул узкий, сначала допускаем повтор исходного кадра,
    # но всё равно не повторяем одного исполнителя.
    for service in candidates:
        if service in result or service.provider_id in provider_ids:
            continue
        result.append(service)
        provider_ids.add(service.provider_id)
        if len(result) >= limit:
            break
    return result


def home(request):
    category_queryset = Category.objects.annotate(
        active_count=Count("services", filter=Q(services__is_active=True))
    )
    category_groups = build_group_context(category_queryset)

    ranked = (
        _card_queryset()
        .annotate(review_total=Count("reviews", distinct=True), rating_avg=Avg("reviews__rating"))
        .order_by("-review_total", "-rating_avg", "-completed_orders", "-created_at")
    )
    popular = _diverse_services(ranked, 8)
    recent = _diverse_services(_card_queryset().order_by("-created_at"), 8)

    # Первый экран специально смешивает разные сферы и исполнителей.
    hero_services = []
    for group_slug in ("beauty", "home", "pets"):
        item = _diverse_services(
            ranked.filter(category__name__in=names_for_group(group_slug)), 1
        )
        if item:
            hero_services.extend(item)
    if len(hero_services) < 3:
        hero_services = popular[:3]

    def collection(group_slug, limit=8):
        return _diverse_services(
            ranked.filter(category__name__in=names_for_group(group_slug)), limit
        )

    featured_candidates = (
        User.objects.filter(services__is_active=True)
        .select_related("profile")
        .annotate(
            services_total=Count("services", filter=Q(services__is_active=True), distinct=True),
            reviews_total=Count("services__reviews", distinct=True),
            rating_avg=Avg("services__reviews__rating"),
        )
        .order_by("-reviews_total", "-rating_avg", "-services_total")
    )
    featured_providers = []
    seen_avatars = set()
    for provider in featured_candidates[:80]:
        avatar = provider.profile.avatar_url
        if avatar in seen_avatars:
            continue
        featured_providers.append(provider)
        seen_avatars.add(avatar)
        if len(featured_providers) >= 8:
            break
    latest_posts = Post.objects.filter(is_published=True).select_related("author").order_by("-created_at")[:3]

    context = {
        "category_groups": category_groups,
        "popular_searches": POPULAR_SEARCHES,
        "popular": popular,
        "recent": recent,
        "hero_services": hero_services,
        "beauty_services": collection("beauty", 8),
        "home_services": collection("home", 8),
        "pet_services": collection("pets", 8),
        "featured_providers": featured_providers,
        "latest_posts": latest_posts,
        "total_categories": Category.objects.count(),
        "total_services": Service.active.count(),
        "total_providers": User.objects.filter(services__is_active=True).distinct().count(),
        "total_reviews": Review.objects.count(),
        "russia_cities": RUSSIA_CITIES,
        "favorite_ids": _favorite_ids(request),
    }
    return render(request, "listings/home.html", context)


def catalog(request):
    services = _card_queryset()

    query = request.GET.get("q", "").strip()
    group_slug = request.GET.get("group", "").strip()
    category_slug = request.GET.get("category", "").strip()
    city = request.GET.get("city", "").strip()
    min_price_raw = request.GET.get("min_price", "").strip()
    max_price_raw = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "new").strip()
    service_format = request.GET.get("format", "").strip()
    min_rating_raw = request.GET.get("rating", "").strip()

    if query:
        terms = [query]
        query_lower = query.lower()
        for trigger, synonyms in SEARCH_SYNONYMS.items():
            if trigger in query_lower:
                terms.extend(synonyms)
        search_q = Q()
        for term in terms:
            search_q |= (Q(title__icontains=term) | Q(description__icontains=term) | Q(category__name__icontains=term) | Q(provider__username__icontains=term) | Q(provider__first_name__icontains=term) | Q(provider__last_name__icontains=term) | Q(provider__profile__headline__icontains=term))
        services = services.filter(search_q).distinct()

    active_category = None
    if category_slug:
        active_category = Category.objects.filter(slug=category_slug).first()
        if active_category:
            services = services.filter(category=active_category)
            matched_group = group_for_category_name(active_category.name)
            if matched_group:
                group_slug = matched_group["slug"]
    elif group_slug:
        group_names = names_for_group(group_slug)
        if group_names:
            services = services.filter(category__name__in=group_names)

    if city:
        services = services.filter(city__iexact=city)
    if service_format:
        services = services.filter(service_format=service_format)
    if min_rating_raw:
        try:
            min_rating_value = float(min_rating_raw)
            services = services.annotate(filter_rating=Avg("reviews__rating")).filter(filter_rating__gte=min_rating_value)
        except ValueError:
            min_rating_raw = ""

    def parse_decimal(raw):
        if not raw:
            return None
        try:
            return Decimal(raw.replace(",", "."))
        except (InvalidOperation, ValueError):
            return None

    min_price = parse_decimal(min_price_raw)
    max_price = parse_decimal(max_price_raw)
    if min_price is not None:
        services = services.filter(price__gte=min_price)
    if max_price is not None:
        services = services.filter(price__lte=max_price)

    if sort == "price_asc":
        services = services.order_by("price", "-created_at")
    elif sort == "price_desc":
        services = services.order_by("-price", "-created_at")
    elif sort == "rating":
        services = services.annotate(rating_sort=Avg("reviews__rating")).order_by("-rating_sort", "-created_at")
    else:
        sort = "new"
        services = services.order_by("-created_at")

    all_categories = Category.objects.annotate(
        active_count=Count("services", filter=Q(services__is_active=True))
    )
    category_groups = build_group_context(all_categories)
    active_group = next((group for group in category_groups if group["slug"] == group_slug), None)
    active_group_categories = active_group["items"] if active_group else []

    cities = list(
        Service.active.exclude(city="")
        .order_by("city")
        .values_list("city", flat=True)
        .distinct()
    )

    paginator = Paginator(services, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "query": query,
        "category_groups": category_groups,
        "active_group": active_group,
        "active_group_slug": group_slug,
        "active_group_categories": active_group_categories,
        "active_category": active_category,
        "cities": cities,
        "city": city,
        "min_price": min_price_raw,
        "max_price": max_price_raw,
        "sort": sort,
        "service_format": service_format,
        "min_rating": min_rating_raw,
        "favorite_ids": _favorite_ids(request),
        "querystring": query_params.urlencode(),
    }
    return render(request, "listings/catalog.html", context)


def service_detail(request, slug):
    service = get_object_or_404(
        Service.objects.select_related("provider", "provider__profile", "category").prefetch_related(
            "photos", "reviews__author"
        ),
        slug=slug,
    )

    user_review = None
    review_form = None
    can_review = False
    completed_order_exists = False
    review_notice = ""
    if request.user.is_authenticated and request.user != service.provider:
        user_review = service.reviews.filter(author=request.user).first()
        completed_order_exists = Order.objects.filter(
            customer=request.user, service=service, status=Order.Status.COMPLETED
        ).exists()
        can_review = completed_order_exists and user_review is None
        if can_review:
            review_form = ReviewForm()
        elif user_review:
            review_notice = "Вы уже оставили отзыв на эту услугу."
        else:
            review_notice = "Отзыв станет доступен после завершённого заказа по этой услуге."

    if request.method == "POST" and request.user.is_authenticated:
        if request.user == service.provider:
            messages.error(request, "Нельзя оставлять отзыв на собственную услугу.")
            return redirect(service.get_absolute_url())
        if user_review:
            messages.error(request, "Вы уже оставили отзыв на эту услугу.")
            return redirect(service.get_absolute_url())
        if not completed_order_exists:
            messages.error(request, "Отзыв можно оставить только после завершённого заказа.")
            return redirect(service.get_absolute_url())
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.service = service
            review.author = request.user
            review.save()
            messages.success(request, "Спасибо! Ваш отзыв опубликован.")
            return redirect(service.get_absolute_url())

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = service.favorited_by.filter(user=request.user).exists()

    similar = []
    if service.category_id:
        similar = list(
            _card_queryset()
            .filter(category=service.category)
            .exclude(pk=service.pk)
            .annotate(rating_sort=Avg("reviews__rating")).order_by("-rating_sort", "-completed_orders", "-created_at")[:6]
        )

    context = {
        "service": service,
        "review_form": review_form,
        "user_review": user_review,
        "review_notice": review_notice,
        "is_owner": request.user == service.provider,
        "is_favorite": is_favorite,
        "similar": similar,
        "favorite_ids": _favorite_ids(request),
    }
    return render(request, "listings/service_detail.html", context)


@login_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        photos_form = ServicePhotosForm(request.POST, request.FILES)
        if form.is_valid() and photos_form.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            if request.user.profile.role == Profile.Role.CUSTOMER:
                request.user.profile.role = Profile.Role.BOTH
                request.user.profile.save(update_fields=["role"])
            _save_photos(request, service)
            messages.success(request, "Услуга опубликована.")
            return redirect(service.get_absolute_url())
    else:
        form = ServiceForm(initial={"is_active": True})
        photos_form = ServicePhotosForm()

    return render(
        request,
        "listings/service_form.html",
        {"form": form, "photos_form": photos_form, "is_new": True, "category_map": {g["slug"]: [name for name, _ in g["items"]] for g in CATEGORY_GROUPS}},
    )


@login_required
def service_edit(request, slug):
    service = get_object_or_404(Service, slug=slug)
    if service.provider != request.user:
        messages.error(request, "Вы не можете редактировать чужую услугу.")
        return redirect(service.get_absolute_url())

    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        photos_form = ServicePhotosForm(request.POST, request.FILES)
        if form.is_valid() and photos_form.is_valid():
            form.save()
            _save_photos(request, service)
            messages.success(request, "Изменения сохранены.")
            return redirect(service.get_absolute_url())
    else:
        form = ServiceForm(instance=service)
        photos_form = ServicePhotosForm()

    return render(
        request,
        "listings/service_form.html",
        {"form": form, "photos_form": photos_form, "service": service, "is_new": False, "category_map": {g["slug"]: [name for name, _ in g["items"]] for g in CATEGORY_GROUPS}},
    )


@login_required
@require_POST
def service_delete(request, slug):
    service = get_object_or_404(Service, slug=slug)
    if service.provider != request.user:
        messages.error(request, "Вы не можете удалить чужую услугу.")
        return redirect(service.get_absolute_url())
    try:
        service.delete()
        messages.success(request, "Услуга удалена.")
    except ProtectedError:
        # Заказы должны сохранять историческую ссылку на услугу. Вместо 500-ошибки
        # архивируем карточку и убираем её из публичного каталога.
        service.is_active = False
        service.save(update_fields=["is_active", "updated_at"])
        messages.info(request, "У услуги есть история заказов, поэтому она перенесена в архив, а не удалена.")
    return redirect("accounts:dashboard")


@login_required
@require_POST
def service_photo_delete(request, photo_id):
    photo = get_object_or_404(ServicePhoto.objects.select_related("service"), pk=photo_id)
    service = photo.service
    if service.provider != request.user:
        messages.error(request, "Вы не можете удалить чужое фото.")
        return redirect(service.get_absolute_url())
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "Фото удалено.")
    return redirect("listings:service_edit", slug=service.slug)


def provider_detail(request, username):
    provider = get_object_or_404(User.objects.select_related("profile"), username=username)
    services = (
        Service.active.filter(provider=provider)
        .select_related("category")
        .prefetch_related("photos", "reviews")
    )
    all_reviews = Review.objects.filter(service__provider=provider)
    avg_rating = all_reviews.aggregate(value=Avg("rating"))["value"]
    reviews_count = all_reviews.count()
    reviews = all_reviews.select_related("author", "service").order_by("-created_at")[:20]
    if avg_rating:
        avg_rating = round(avg_rating, 1)
    completed_orders = Order.objects.filter(provider=provider, status=Order.Status.COMPLETED).count()
    response_text = "отвечает в течение часа"
    if provider.profile.response_time_minutes <= 15:
        response_text = f"обычно отвечает за {provider.profile.response_time_minutes} мин"
    elif provider.profile.response_time_minutes < 60:
        response_text = f"обычно отвечает за {provider.profile.response_time_minutes} мин"
    portfolio = [item for service in services for item in service.photos.all()][:9]
    return render(
        request,
        "listings/provider_detail.html",
        {"provider": provider, "services": services, "reviews": reviews, "avg_rating": avg_rating, "reviews_count": reviews_count, "profile_cover_service": services.first(), "completed_orders": completed_orders or provider.profile.completed_orders, "response_text": response_text, "portfolio": portfolio, "portfolio_services": list(services[:6]), "favorite_ids": _favorite_ids(request)},
    )


def _save_photos(request, service):
    max_photos = 6
    existing_count = service.photos.count()
    files = request.FILES.getlist("photos")
    available = max(0, max_photos - existing_count)
    for image in files[:available]:
        ServicePhoto.objects.create(service=service, image=image)
    if len(files) > available:
        messages.warning(request, f"Можно хранить не больше {max_photos} фотографий. Лишние файлы не добавлены.")
