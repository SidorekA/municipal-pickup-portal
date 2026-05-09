#core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pickups.models import Pickup
from notifications.models import Notification

@login_required
def home_view(request):
    """Widok strony głównej (Dashboard)."""
    context = {}

    if not request.user.is_superuser:
        recent_pickups = Pickup.objects.filter(reporter=request.user).order_by('-created_at')[:3]
        context['recent_pickups'] = recent_pickups
    else:
        recent_pickups = Pickup.objects.all().order_by('-created_at')[:3]
        context['recent_pickups'] = recent_pickups

    # Pobieranie nieprzeczytanych powiadomień
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    context['unread_notifications'] = unread_notifications

    return render(request, 'core/home.html', context)