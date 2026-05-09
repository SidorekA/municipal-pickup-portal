#core/views.py


from django.apps import apps
from django.http import HttpResponse
import pandas as pd
from .models import DataTransferLog
from django.db import transaction

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pickups.models import Pickup
from notifications.models import Notification

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
import urllib.parse

from reports.models import MonthlyConfirmation
from reports.services import import_collection_data
from users.models import Coordinator, Permission

User = get_user_model()



EXCLUDED_APPS = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']

@staff_member_required
def admin_tasks_view(request):
    """Widok panelu zadań administracyjnych."""
    # Pobranie wszystkich modeli z zainstalowanych aplikacji, z wykluczeniem systemowych
    models_list = []
    for app_config in apps.get_app_configs():
        if app_config.name not in EXCLUDED_APPS:
            for model in app_config.get_models():
                model_name = f"{app_config.label}.{model.__name__}"
                models_list.append((model_name, model._meta.verbose_name.title()))

    models_list.sort(key=lambda x: x[1])

    # Pobranie rejestru transferów
    transfer_logs = DataTransferLog.objects.all().order_by('-created_at')[:20]

    context = {
        'models_list': models_list,
        'transfer_logs': transfer_logs,
    }
    return render(request, 'core/admin_tasks.html', context)

@staff_member_required
def export_table_data_view(request):
    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        export_format = request.POST.get('export_format')

        if not model_name or not export_format:
            messages.error(request, "Wybierz tabelę i format eksportu.")
            return redirect('core:admin_tasks')

        try:
            app_label, model_class_name = model_name.split('.')
            if app_label in EXCLUDED_APPS:
                messages.error(request, "Eksport z tej tabeli jest zabroniony.")
                return redirect('core:admin_tasks')
            model = apps.get_model(app_label, model_class_name)
        except LookupError:
            messages.error(request, "Nieprawidłowa tabela.")
            return redirect('core:admin_tasks')

        queryset = model.objects.all()
        data = list(queryset.values())
        df = pd.DataFrame(data)

        # Remove timezone info for excel
        for col in df.select_dtypes(['datetimetz']).columns:
            df[col] = df[col].dt.tz_localize(None)

        file_name = f"{app_label}_{model_class_name}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

        response = HttpResponse()

        try:
            if export_format == 'csv':
                response['Content-Type'] = 'text/csv'
                response['Content-Disposition'] = f'attachment; filename={file_name}.csv'
                df.to_csv(path_or_buf=response, index=False, encoding='utf-8')
            elif export_format == 'xlsx':
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)

            # Zapis do logu
            # Zapis do logu
            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=len(df),
                status='SUCCESS',
                created_by=request.user
            )
            return response

        except Exception as e:
            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=0,
                status='ERROR',
                details=str(e),
                created_by=request.user
            )
            messages.error(request, f"Błąd eksportu: {str(e)}")
            return redirect('core:admin_tasks')

    return redirect('core:admin_tasks')

@staff_member_required
def import_table_data_view(request):
    if request.method == 'POST' and request.FILES.get('data_file'):
        model_name = request.POST.get('model_name')
        data_file = request.FILES['data_file']

        if not model_name:
            messages.error(request, "Wybierz tabelę do importu.")
            return redirect('core:admin_tasks')

        if not data_file.name.endswith(('.xlsx', '.csv')):
            messages.error(request, "Nieprawidłowy format pliku. Proszę wgrać plik .xlsx lub .csv")
            return redirect('core:admin_tasks')

        try:
            app_label, model_class_name = model_name.split('.')
            if app_label in EXCLUDED_APPS:
                messages.error(request, "Import do tej tabeli jest zabroniony.")
                return redirect('core:admin_tasks')
            model = apps.get_model(app_label, model_class_name)
        except LookupError:
            messages.error(request, "Nieprawidłowa tabela.")
            return redirect('core:admin_tasks')

        try:
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)

            # Remove NaNs
            df = df.where(pd.notnull(df), None)

            records_created = 0
            records_updated = 0
            errors = []

            # Pobieranie wszystkich relacji FK, aby poprawić mapowanie
            fk_fields = {f.name: f for f in model._meta.fields if f.is_relation and f.many_to_one}

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        with transaction.atomic():
                            row_dict = row.to_dict()
                            clean_dict = {}

                            for key, value in row_dict.items():
                                if pd.isna(value):
                                    clean_dict[key] = None
                                else:
                                    clean_dict[key] = value

                                # Konwersja _id fields if present
                                if key in fk_fields and key + '_id' not in clean_dict:
                                    pass

                            if 'id' in clean_dict and clean_dict['id'] is not None:
                                obj_id = clean_dict.pop('id')
                                obj, created = model.objects.update_or_create(id=obj_id, defaults=clean_dict)
                                if created:
                                    records_created += 1
                                else:
                                    records_updated += 1
                            else:
                                clean_dict.pop('id', None)
                                obj, created = model.objects.get_or_create(**clean_dict)
                                if created:
                                    records_created += 1

                    except Exception as e:
                        errors.append(f"Wiersz {index+2}: {str(e)}")

            status = 'SUCCESS'
            details = f"Utworzono: {records_created}, Zaktualizowano/Pominięto: {records_updated}"
            if errors:
                status = 'PARTIAL' if records_created > 0 or records_updated > 0 else 'ERROR'
                details += "\nBłędy:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    details += f"\n...oraz {len(errors) - 10} innych."

            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=len(df),
                status=status,
                details=details,
                created_by=request.user
            )

            if status in ['SUCCESS', 'PARTIAL']:
                msg = f"Import zakończony. Utworzono: {records_created}, Zaktualizowano: {records_updated}."
                if errors:
                    messages.warning(request, f"{msg} Wystąpiły błędy (sprawdź rejestr).")
                else:
                    messages.success(request, msg)
            else:
                messages.error(request, "Import zakończony niepowodzeniem (sprawdź rejestr).")

        except Exception as e:
            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=0,
                status='ERROR',
                details=str(e),
                created_by=request.user
            )
            messages.error(request, f"Błąd podczas parsowania pliku: {str(e)}")

    return redirect('core:admin_tasks')

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
                if count == 1:
                    return f"{count} rekord"
                elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                    return f"{count} rekordy"
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

    # Pobieranie nieprzeczytanych powiadomień
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    context['unread_notifications'] = unread_notifications

    return render(request, 'core/home.html', context)