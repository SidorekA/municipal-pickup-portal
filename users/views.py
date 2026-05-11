# users/views.py
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import UserBasicForm, UserProfileForm, StyledPasswordChangeForm
from .models import UserProfile


@login_required
def profile_view(request):
    """Podgląd i edycja profilu użytkownika."""
    # Utwórz profil jeśli nie istnieje (np. stare konta bez profilu)
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'department_short': '',
            'department_name': '',
        }
    )

    if request.method == 'POST':
        user_form    = UserBasicForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profil został zaktualizowany.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Popraw błędy w formularzu.')
    else:
        user_form    = UserBasicForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    # Uprawnienia użytkownika do wyświetlenia na profilu
    from users.models import Permission
    permissions = Permission.objects.filter(
        user=request.user, active=True
    ).select_related('mpk_number').order_by('mpk_number__mpk_number')

    return render(request, 'users/profile.html', {
        'user_form':    user_form,
        'profile_form': profile_form,
        'permissions':  permissions,
    })


@login_required
def change_password_view(request):
    """Zmiana hasła z zachowaniem sesji."""
    if request.method == 'POST':
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Bez tego Django wyloguje użytkownika po zmianie hasła
            update_session_auth_hash(request, user)
            messages.success(request, 'Hasło zostało zmienione.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Popraw błędy w formularzu.')
    else:
        form = StyledPasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})