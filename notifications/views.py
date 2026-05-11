from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
@require_POST
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if notification.is_global:
        notification.read_by.add(request.user)
    elif notification.user == request.user:
        notification.is_read = True
        notification.save()
    return redirect('home')
