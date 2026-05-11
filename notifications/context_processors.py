from .models import Notification

def unread_notifications_count(request):
    """
    Wstrzykuje liczbę nieprzeczytanych powiadomień do każdego szablonu.
    Używany w navbar do wyświetlenia badge'a na ikonie dzwonka.
    """
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return {'unread_notifications_count': count}
