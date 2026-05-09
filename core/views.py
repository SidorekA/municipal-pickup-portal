#core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pickups.models import Pickup

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

    return render(request, 'core/home.html', context)