from django.db.models import Q

from .models import Favorite, Message


def marketplace_counts(request):
    if not request.user.is_authenticated:
        return {"nav_favorites_count": 0, "nav_unread_count": 0}
    return {
        "nav_favorites_count": Favorite.objects.filter(user=request.user).count(),
        "nav_unread_count": Message.objects.filter(
            Q(conversation__customer=request.user) | Q(conversation__provider=request.user),
            is_read=False,
        ).exclude(sender=request.user).count(),
    }
