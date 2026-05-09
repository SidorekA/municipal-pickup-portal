#core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pickups.models import Pickup

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
import urllib.parse

from reports.models import MonthlyConfirmation
from reports.services import import_collection_data
from users.models import Coordinator, Permission

User = get_user_model()


@staff_member_required
def admin_tasks_view(request):
    """Widok panelu zadań administracyjnych."""
    return render(request, 'core/admin_tasks.html')

@staff_member_required
def import_collection_data_view(request):
    """Zadanie importu danych z Excela."""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith(('.xlsx', '.csv')):
            messages.error(request, 'Nieprawidłowy format pliku. Proszę wgrać plik .xlsx lub .csv')
            return redirect('core:admin_tasks')

        try:
            results = import_collection_data(excel_file, request.user)

            # Helper do odmiany słowa "rekord" (zapożyczony z reports)
            def _odmien_rekord(count):
                if count == 1: return f"{count} rekord"
                elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20): return f"{count} rekordy"
                return f"{count} rekordów"

            parts = []
            if results['imported'] > 0:
                parts.append(f"Zaimportowano {_odmien_rekord(results['imported'])}.")
            if results['skipped'] > 0:
                parts.append(f"{_odmien_rekord(results['skipped'])} pominięto – istnieją już w bazie.")
            if results['auto_confirmed'] > 0:
                parts.append(f"Automatycznie potwierdzono {_odmien_rekord(results['auto_confirmed'])}.")

            if parts:
                messages.success(request, ' '.join(parts))

            if results['errors']:
                for error in results['errors'][:5]:
                    messages.error(request, error)
                if len(results['errors']) > 5:
                    messages.error(request, f"...oraz {len(results['errors']) - 5} innych błędów.")

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas importu: {str(e)}")

    return redirect('core:admin_tasks')


@staff_member_required
def draft_email_unconfirmed_view(request):
    """Generowanie draftu e-maila do użytkowników bez potwierdzenia zestawienia."""
    today = timezone.now().date()
    current_month_start = datetime.date(today.year, today.month, 1)

    unconfirmed_mpks = MonthlyConfirmation.objects.filter(
        month=current_month_start
    ).exclude(status='ZATWIERDZONE').values_list('mpk_number', flat=True)

    users = Permission.objects.filter(
        mpk_number__in=unconfirmed_mpks,
        active=True,
        user__is_active=True
    ).exclude(user__email='').values_list('user__email', flat=True).distinct()

    emails = ",".join(users)

    subject = "Przypomnienie: Brak potwierdzenia zestawienia miesięcznego"
    body = """Dzień dobry,

Przypominamy o obowiązku potwierdzenia zestawienia miesięcznego odbioru odpadów w systemie.

Pozdrawiamy,
Administrator"""

    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)

    mailto_url = f"mailto:{emails}?subject={safe_subject}&body={safe_body}"
    messages.info(request, "Przygotowano draft maila - otwórz program pocztowy aby wysłać.")

    return render(request, 'core/email_draft.html', {'mailto_url': mailto_url, 'title': 'Wygeneruj e-mail'})

@staff_member_required
def draft_email_all_users_view(request):
    """Generowanie draftu e-maila do wszystkich użytkowników."""
    users = User.objects.filter(is_active=True).exclude(email='')
    emails = ",".join(users.values_list('email', flat=True))

    subject = "Informacja z systemu Zarządzania Odpadami"
    body = """Dzień dobry,

"""

    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)

    mailto_url = f"mailto:{emails}?subject={safe_subject}&body={safe_body}"

    return render(request, 'core/email_draft.html', {'mailto_url': mailto_url, 'title': 'E-mail do wszystkich użytkowników'})

@staff_member_required
def draft_email_coordinators_view(request):
    """Generowanie draftu e-maila do Koordynatorów MPKów."""
    coordinators = Coordinator.objects.filter(active=True).select_related('user')
    emails = ",".join(set([c.user.email for c in coordinators if c.user.email]))

    subject = "Informacja dla Koordynatorów MPK"
    body = """Dzień dobry Koordynatorzy,

"""

    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)

    mailto_url = f"mailto:{emails}?subject={safe_subject}&body={safe_body}"

    return render(request, 'core/email_draft.html', {'mailto_url': mailto_url, 'title': 'E-mail do Koordynatorów'})


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