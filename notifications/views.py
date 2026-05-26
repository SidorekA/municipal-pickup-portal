from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Notification

@require_POST
def mark_as_read(request, pk):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), 'login')

    notification = get_object_or_404(Notification, pk=pk)
    
    # 1. Zapis stanu powiadomienia
    if getattr(notification, 'is_global', False):
        notification.read_by.add(request.user)
    else:
        # Zamiast porównywać obiekty leniwe, wysyłamy twarde polecenie do bazy
        Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    
    # 2. Odpowiedź dla JavaScriptu (nasz fetch z topbaru)
    if is_ajax:
        return JsonResponse({"status": "success", "message": "Oznaczono jako przeczytane"})
    
    # 3. Odpowiedź dla zwykłego kliknięcia (np. ze strony notification_list.html)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@require_POST
def mark_all_as_read(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), 'login')

    # Aktualizacja powiadomień indywidualnych
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    
    if is_ajax:
        return JsonResponse({"status": "success", "message": "Wszystkie powiadomienia zostały przeczytane"})

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')

    global_notifications = Notification.objects.none()
    if request.user.is_staff:
        global_notifications = Notification.objects.filter(
            is_global=True
        ).order_by('-created_at')

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'global_notifications': global_notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    })