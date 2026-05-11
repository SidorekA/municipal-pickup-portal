# notifications/context_processors.py
from .models import Notification


def unread_notifications_count(request):
    """
    Wstrzykuje liczbę nieprzeczytanych powiadomień do każdego szablonu.
    Wymagane: zarejestrowanie w TEMPLATES context_processors w settings.
    """
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return {'unread_notifications_count': count}