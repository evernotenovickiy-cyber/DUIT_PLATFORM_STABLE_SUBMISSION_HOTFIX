from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Service
from accounts.models import Profile

from .forms import MessageForm, OrderForm, PaymentForm
from .models import Conversation, Favorite, Message, Order, Payment


@login_required
def favorites(request):
    items = Favorite.objects.filter(user=request.user).select_related(
        "service", "service__provider", "service__category"
    ).prefetch_related("service__photos", "service__reviews")
    return render(request, "marketplace/favorites.html", {"items": items})


@login_required
@require_POST
def favorite_toggle(request, service_id):
    service = get_object_or_404(Service.active, pk=service_id)
    favorite = Favorite.objects.filter(user=request.user, service=service).first()
    if favorite:
        favorite.delete()
        active = False
        messages.info(request, "Услуга удалена из избранного.")
    else:
        Favorite.objects.create(user=request.user, service=service)
        active = True
        messages.success(request, "Услуга добавлена в избранное.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "favorite": active})
    return redirect(request.POST.get("next") or service.get_absolute_url())


@login_required
def order_create(request, service_id):
    service = get_object_or_404(Service.active.select_related("provider"), pk=service_id)
    if request.user == service.provider:
        messages.error(request, "Нельзя заказать собственную услугу.")
        return redirect(service.get_absolute_url())

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.provider = service.provider
            order.service = service
            order.price = service.price
            order.save()
            # Если пользователь регистрировался только как исполнитель, но сам оформил
            # заказ, его аккаунт становится универсальным — иначе заказ был бы скрыт
            # в кабинете исполнителя.
            if request.user.profile.role == Profile.Role.PROVIDER:
                request.user.profile.role = Profile.Role.BOTH
                request.user.profile.save(update_fields=["role"])
            Conversation.objects.get_or_create(
                customer=request.user, provider=service.provider, service=service
            )
            Payment.objects.get_or_create(order=order, defaults={"amount": order.price})
            messages.success(request, f"Заказ #{order.pk} создан. Выберите способ оплаты.")
            return redirect("marketplace:payment_checkout", order_id=order.pk)
    else:
        form = OrderForm()
    return render(request, "marketplace/order_create.html", {"service": service, "form": form})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("service", "customer", "provider"), pk=order_id
    )
    if not order.can_view(request.user):
        messages.error(request, "У вас нет доступа к этому заказу.")
        return redirect("accounts:dashboard")
    conversation, _ = Conversation.objects.get_or_create(
        customer=order.customer, provider=order.provider, service=order.service
    )
    payment, _ = Payment.objects.get_or_create(order=order, defaults={"amount": order.price})
    return render(request, "marketplace/order_detail.html", {"order": order, "conversation": conversation, "payment": payment})


@login_required
@require_POST
def order_status(request, order_id, status):
    order = get_object_or_404(Order, pk=order_id)
    if not order.can_view(request.user):
        messages.error(request, "Недостаточно прав.")
        return redirect("accounts:dashboard")

    provider_transitions = {
        Order.Status.NEW: {Order.Status.ACCEPTED, Order.Status.CANCELLED},
        Order.Status.ACCEPTED: {Order.Status.IN_PROGRESS, Order.Status.CANCELLED},
        Order.Status.IN_PROGRESS: {Order.Status.COMPLETED, Order.Status.CANCELLED},
    }
    customer_transitions = {
        Order.Status.NEW: {Order.Status.CANCELLED},
        Order.Status.ACCEPTED: {Order.Status.CANCELLED},
    }
    allowed = provider_transitions if request.user == order.provider else customer_transitions
    valid_values = {choice for choice, _ in Order.Status.choices}
    if status not in valid_values or status not in allowed.get(order.status, set()):
        messages.error(request, "Этот переход статуса недоступен.")
        return redirect("marketplace:order_detail", order_id=order.pk)

    order.status = status
    order.save(update_fields=["status", "updated_at"])
    if status == Order.Status.CANCELLED:
        payment = Payment.objects.filter(order=order, status=Payment.Status.PAID).first()
        if payment:
            payment.status = Payment.Status.REFUNDED
            payment.refunded_at = timezone.now()
            payment.save(update_fields=["status", "refunded_at", "updated_at"])
            messages.info(request, f"Учебная оплата {payment.amount:.0f} ₽ помечена как возвращённая.")
    messages.success(request, f"Статус заказа: {order.get_status_display()}.")
    return redirect("marketplace:order_detail", order_id=order.pk)


@login_required
def payment_checkout(request, order_id):
    order = get_object_or_404(Order.objects.select_related("service", "provider", "customer"), pk=order_id)
    if request.user != order.customer:
        messages.error(request, "Оплатить заказ может только заказчик.")
        return redirect("marketplace:order_detail", order_id=order.pk)
    payment, _ = Payment.objects.get_or_create(order=order, defaults={"amount": order.price})
    if order.status == Order.Status.CANCELLED:
        messages.error(request, "Отменённый заказ нельзя оплачивать.")
        return redirect("marketplace:order_detail", order_id=order.pk)
    if payment.status == Payment.Status.REFUNDED:
        messages.info(request, "Платёж по этому заказу уже возвращён.")
        return redirect("marketplace:order_detail", order_id=order.pk)
    if payment.status == Payment.Status.PAID:
        messages.info(request, "Этот заказ уже оплачен.")
        return redirect("marketplace:order_detail", order_id=order.pk)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data["method"]
            payment.amount = order.price
            payment.method = method
            payment.failure_reason = ""
            if method == Payment.Method.AFTER_SERVICE:
                payment.status = Payment.Status.PENDING
                payment.transaction_id = ""
                payment.card_last4 = ""
                payment.paid_at = None
                payment.save()
                messages.success(request, "Выбрана оплата после выполнения. Банковские данные не требуются.")
                return redirect("marketplace:order_detail", order_id=order.pk)

            card_number = form.cleaned_data["card_number"]
            payment.card_last4 = card_number[-4:]
            payment.transaction_id = f"DUIT-{order.pk:06d}-{timezone.now():%H%M%S}"
            if card_number == PaymentForm.DECLINED_CARD:
                payment.status = Payment.Status.FAILED
                payment.failure_reason = "Тестовый отказ банка"
                payment.paid_at = None
                payment.save()
                messages.error(request, "Тестовый банк отклонил платёж. Попробуйте карту 4242 4242 4242 4242.")
            else:
                payment.status = Payment.Status.PAID
                payment.paid_at = timezone.now()
                payment.save()
                messages.success(request, f"Учебная оплата {payment.amount:.0f} ₽ прошла успешно.")
                return redirect("marketplace:payment_success", order_id=order.pk)
    else:
        initial_method = payment.method if payment.method in {Payment.Method.CARD, Payment.Method.AFTER_SERVICE} else Payment.Method.CARD
        form = PaymentForm(initial={"method": initial_method})

    return render(request, "marketplace/payment_checkout.html", {"order": order, "payment": payment, "form": form})


@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order.objects.select_related("service", "provider"), pk=order_id, customer=request.user)
    payment = get_object_or_404(Payment, order=order)
    if payment.status != Payment.Status.PAID:
        return redirect("marketplace:payment_checkout", order_id=order.pk)
    return render(request, "marketplace/payment_success.html", {"order": order, "payment": payment})


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        Q(customer=request.user) | Q(provider=request.user)
    ).select_related("customer", "customer__profile", "provider", "provider__profile", "service").prefetch_related("messages")
    return render(request, "marketplace/inbox.html", {"conversations": conversations})


@login_required
@require_POST
def conversation_start(request, service_id):
    service = get_object_or_404(Service.active.select_related("provider"), pk=service_id)
    if request.user == service.provider:
        messages.info(request, "Это ваша услуга.")
        return redirect(service.get_absolute_url())
    conversation, _ = Conversation.objects.get_or_create(
        customer=request.user, provider=service.provider, service=service
    )
    return redirect("marketplace:conversation", conversation_id=conversation.pk)


def _get_conversation_for_user(user, conversation_id):
    return get_object_or_404(
        Conversation.objects.select_related("customer", "provider", "service"),
        Q(customer=user) | Q(provider=user),
        pk=conversation_id,
    )


@login_required
def conversation(request, conversation_id):
    conv = _get_conversation_for_user(request.user, conversation_id)
    Message.objects.filter(conversation=conv, is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conv
            msg.sender = request.user
            msg.save()
            Conversation.objects.filter(pk=conv.pk).update(updated_at=msg.created_at)
            return redirect("marketplace:conversation", conversation_id=conv.pk)
    else:
        form = MessageForm()

    thread = conv.messages.select_related("sender").all()
    return render(request, "marketplace/conversation.html", {"conversation": conv, "thread": thread, "form": form})


@login_required
def conversation_messages_json(request, conversation_id):
    conv = _get_conversation_for_user(request.user, conversation_id)
    Message.objects.filter(conversation=conv, is_read=False).exclude(sender=request.user).update(is_read=True)
    data = [
        {
            "id": message.pk,
            "sender": message.sender.username,
            "sender_id": message.sender_id,
            "text": message.text,
            "created_at": message.created_at.strftime("%H:%M"),
            "mine": message.sender_id == request.user.id,
        }
        for message in conv.messages.select_related("sender").all()
    ]
    return JsonResponse({"messages": data})
