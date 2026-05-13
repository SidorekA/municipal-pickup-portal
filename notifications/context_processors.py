from .models import Notification

def unread_notifications_count(request):
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0, 'recent_notifications': []}

    qs = Notification.objects.filter(
        user=request.user,
        is_read=False,
        is_active=True
    ).order_by('-created_at')

    return {
        'unread_notifications_count': qs.count(),
        'recent_notifications': qs[:10],
    }