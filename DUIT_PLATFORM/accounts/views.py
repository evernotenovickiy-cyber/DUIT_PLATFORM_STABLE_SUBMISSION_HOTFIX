from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import redirect, render

from listings.models import Service
from marketplace.models import Conversation, Favorite, Message, Order, Payment

from .forms import ProfileForm, RegisterForm
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Добро пожаловать в DUIT, {user.first_name or user.username}!")
            return redirect("accounts:dashboard")
    else:
        requested_role = request.GET.get("role", Profile.Role.CUSTOMER)
        if requested_role not in {Profile.Role.CUSTOMER, Profile.Role.PROVIDER, Profile.Role.BOTH}:
            requested_role = Profile.Role.CUSTOMER
        form = RegisterForm(initial={"role": requested_role})
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    profile = request.user.profile
    requested_mode = request.GET.get("mode", "")
    if profile.role == Profile.Role.CUSTOMER:
        mode = "customer"
    elif profile.role == Profile.Role.PROVIDER:
        mode = "provider"
    else:
        mode = requested_mode if requested_mode in {"customer", "provider"} else request.session.get("dashboard_mode", "customer")
    request.session["dashboard_mode"] = mode

    tab = request.GET.get("tab", "overview")
    services = Service.objects.filter(provider=request.user).select_related("category").prefetch_related("photos", "reviews")
    provider_orders = Order.objects.filter(provider=request.user).select_related("service", "customer")
    customer_orders = Order.objects.filter(customer=request.user).select_related("service", "provider")
    favorites = Favorite.objects.filter(user=request.user).select_related("service", "service__provider", "service__category").prefetch_related("service__photos", "service__reviews")
    conversations = Conversation.objects.filter(Q(customer=request.user) | Q(provider=request.user)).select_related("customer", "provider", "service").prefetch_related("messages")
    completed_provider_orders = provider_orders.filter(status=Order.Status.COMPLETED)
    paid_provider_orders = provider_orders.filter(payment__status=Payment.Status.PAID)
    total_revenue = paid_provider_orders.aggregate(total=Sum("price"))["total"] or 0
    pending_payments = provider_orders.filter(payment__status=Payment.Status.PENDING).aggregate(total=Sum("price"))["total"] or 0
    avg_rating = Service.objects.filter(provider=request.user).aggregate(value=Avg("reviews__rating"))["value"]
    total_reviews = Service.objects.filter(provider=request.user).aggregate(value=Count("reviews"))["value"] or 0
    unread_count = Message.objects.filter(Q(conversation__customer=request.user) | Q(conversation__provider=request.user), is_read=False).exclude(sender=request.user).count()

    provider_tabs = {"overview", "services", "incoming"}
    customer_tabs = {"overview", "orders", "favorites"}
    allowed_tabs = provider_tabs if mode == "provider" else customer_tabs
    if tab not in allowed_tabs:
        tab = "overview"

    context = {
        "tab": tab,
        "mode": mode,
        "can_switch_mode": profile.role == Profile.Role.BOTH,
        "services": services,
        "profile": profile,
        "provider_orders": provider_orders,
        "customer_orders": customer_orders,
        "favorites": favorites,
        "conversations": conversations,
        "unread_count": unread_count,
        "stats": {
            "services": services.count(),
            "incoming_orders": provider_orders.exclude(status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED]).count(),
            "my_orders": customer_orders.exclude(status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED]).count(),
            "favorites": favorites.count(),
            "unread": unread_count,
            "completed": completed_provider_orders.count(),
            "revenue": total_revenue,
            "pending_payments": pending_payments,
            "rating": round(avg_rating, 1) if avg_rating else None,
            "reviews": total_reviews,
        },
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("accounts:dashboard")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile_edit.html", {"form": form})
