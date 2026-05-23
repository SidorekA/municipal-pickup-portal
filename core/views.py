#core/views.py


from django.apps import apps
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from django.http import HttpResponse
import pandas as pd

from scheduling.services import get_next_pickup_date
from .models import DataTransferLog
from django.db import transaction
from .services import generate_auditlog_export

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from pickups.models import Pickup
from django.db.models import Count
from notifications.models import Notification
from core.forms import GlobalAnnouncementForm

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone, formats
import datetime
from django.contrib.auth import get_user_model
import urllib.parse

from locations.models import MPKNumber
from reports.models import MonthlyConfirmation, SummaryCollectionSchedule
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

    transfer_logs = DataTransferLog.objects.all().order_by('-created_at')[:20]

    # Pobieranie ContentTypes używanych w logach
    log_content_type_ids = LogEntry.objects.values_list('content_type_id', flat=True).distinct()
    log_content_types = ContentType.objects.filter(id__in=log_content_type_ids).order_by('model')

    # Pobieranie Użytkowników
    users = User.objects.filter(is_active=True).order_by('username')
    mpk_numbers = MPKNumber.objects.filter(active=True).order_by('mpk_number')

    # Pobierz dostępne lata z istniejących zestawień, jeśli nie ma to daj np. obecny rok
    years = SummaryCollectionSchedule.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not years:
        years = [timezone.now().year]

    months = [
        (1, 'Styczeń'), (2, 'Luty'), (3, 'Marzec'), (4, 'Kwiecień'),
        (5, 'Maj'), (6, 'Czerwiec'), (7, 'Lipiec'), (8, 'Sierpień'),
        (9, 'Wrzesień'), (10, 'Październik'), (11, 'Listopad'), (12, 'Grudzień')
    ]

    # Global announcements
    active_announcements = Notification.objects.filter(is_global=True, is_active=True).order_by('-created_at')
    form_announcement = GlobalAnnouncementForm()

    context = {
        'models_list': models_list,
        'transfer_logs': transfer_logs,
        'log_content_types': log_content_types,
        'users': users,
        'mpk_numbers': mpk_numbers,
        'years': years,
        'months': months,
        'active_announcements': active_announcements,
        'form_announcement': form_announcement,
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

            df = df.where(pd.notnull(df), None)

            records_created = 0
            records_updated = 0
            errors = []

            fk_fields = {f.name: f for f in model._meta.fields if f.is_relation and f.many_to_one}

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        with transaction.atomic():
                            row_dict = row.to_dict()
                            clean_dict = {}

                            for key, value in row_dict.items():
                                # Znajdź prawdziwą nazwę pola (bez dopisku _id z Pandas)
                                field_name = key[:-3] if key.endswith('_id') else key
                                
                                try:
                                    field = model._meta.get_field(field_name)
                                    is_char = field.get_internal_type() in ['CharField', 'TextField']
                                except Exception:
                                    is_char = False

                                if pd.isna(value):
                                    if is_char:
                                        clean_dict[key] = ""
                                else:
                                    # Zabezpieczenie przed liczbami z Excela (np. "697612038.0" -> 697612038)
                                    if isinstance(value, float) and value.is_integer():
                                        clean_dict[key] = int(value)
                                    else:
                                        clean_dict[key] = value

                            if 'id' in clean_dict and clean_dict['id'] is not None:
                                obj_id = clean_dict.pop('id')
                                obj, created = model.objects.update_or_create(id=obj_id, defaults=clean_dict)
                                if created:
                                    records_created += 1
                                else:
                                    records_updated += 1
                            else:
                                clean_dict.pop('id', None)
                                # Zamiast nieprzewidywalnego get_or_create używamy prostej metody create()
                                obj = model.objects.create(**clean_dict)
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
    today = timezone.now()
    today_date = today.date()
    first_day_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 1. UPRAWNIENIA - Pobieramy MPK, do których użytkownik ma dostęp
    allowed_mpk_ids = []
    if not request.user.is_superuser:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, active=True
        ).values_list('mpk_number_id', flat=True)

    # 2. OSTATNIE ZGŁOSZENIA (Dla nowej karty "Historia")
    if request.user.is_superuser:
        recent_pickups_qs = Pickup.objects.all()
    else:
        recent_pickups_qs = Pickup.objects.filter(mpk_number_id__in=allowed_mpk_ids)
        
    recent_pickups = list(recent_pickups_qs.select_related(
        'mpk_number', 'location', 'reporter'
    ).prefetch_related(
        'waste_bins__waste_fraction__fraction_type__schedules'
    ).order_by('-created_at')[:5])
        
    for pickup in recent_pickups:
        for bin in pickup.waste_bins.all():
            bin.planned_date = get_next_pickup_date(
                fraction_type=bin.waste_fraction.fraction_type,
                submitted_at=pickup.reported_at
            )
    context['object_list'] = recent_pickups 
    context['recent_pickups'] = recent_pickups

    # 3. POWIADOMIENIA
    context['unread_notifications'] = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    context['now'] = today

    # 4. KPI & STATYSTYKI ZGŁOSZEŃ
    last_day_prev_month = first_day_month - datetime.timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if request.user.is_superuser:
        pickups_qs = Pickup.objects.filter(reported_at__gte=first_day_month)
        active_pickups_for_date = Pickup.objects.filter(
            status__in=['NOWE', 'WYSŁANE', 'POTWIERDZONE']
        ).select_related('mpk_number').prefetch_related('waste_bins__waste_fraction__fraction_type__schedules')
        pickups_prev_qs = Pickup.objects.filter(
            reported_at__gte=first_day_prev_month, 
            reported_at__lt=first_day_month
        )
    else:
        pickups_qs = Pickup.objects.filter(
            reported_at__gte=first_day_month,
            mpk_number_id__in=allowed_mpk_ids
        )
        pickups_prev_qs = Pickup.objects.filter(
            reported_at__gte=first_day_prev_month,
            reported_at__lt=first_day_month,
            mpk_number_id__in=allowed_mpk_ids
        )
        active_pickups_for_date = Pickup.objects.filter(
            mpk_number_id__in=allowed_mpk_ids,
            status__in=['NOWE', 'WYSŁANE', 'POTWIERDZONE']
        ).select_related('mpk_number').prefetch_related('waste_bins__waste_fraction__fraction_type__schedules')

# Obliczanie trendu procentowego
    current_count = pickups_qs.count()
    prev_count = pickups_prev_qs.count()

    if prev_count > 0:
        trend_pct = round(((current_count - prev_count) / prev_count) * 100)
    else:
        # Jeśli w poprzednim miesiącu było 0, a teraz jest >0, to wzrost wynosi 100%
        trend_pct = 100 if current_count > 0 else 0

    context['kpi'] = {
        'pickups_this_month': pickups_qs.count(),
        'pickups_pending': pickups_qs.filter(status='NOWE').count(),
        'unconfirmed_mpks': MonthlyConfirmation.objects.filter(
            month=first_day_month.date().replace(day=1),
            status='OCZEKUJE'
        ).count(),
        'current_month_name': formats.date_format(today, "F Y"),
        'pickups_trend_pct': trend_pct,
    }

    # 5. NOWA LOGIKA: OBLICZANIE NASTĘPNEGO ODBIORU
    closest_date = None
    next_pickup_data = None

    for pickup in active_pickups_for_date:
        for bin in pickup.waste_bins.all():
            planned_date = get_next_pickup_date(
                fraction_type=bin.waste_fraction.fraction_type,
                submitted_at=pickup.reported_at
            )
            
            if planned_date and planned_date >= today_date:
                if closest_date is None or planned_date < closest_date:
                    closest_date = planned_date
                    next_pickup_data = {
                        'scheduled_date': planned_date,
                        'fraction_name': bin.waste_fraction.fraction_type.name,
                        'mpk_name': pickup.mpk_number.mpk_number if pickup.mpk_number else "Nieznany MPK"
                    }

    # Dodajemy wyliczone dane do kontekstu dla szablonu home.html
    context['next_pickup'] = next_pickup_data

    # 6. WYKRES (Ostatnie 5 miesięcy)
    monthly_counts = []
    for i in range(4, -1, -1):
        target = (first_day_month - datetime.timedelta(days=i * 28)).replace(day=1)
        if target.month == 12:
            next_month = target.replace(year=target.year + 1, month=1)
        else:
            next_month = target.replace(month=target.month + 1)

        count = Pickup.objects.filter(
            reported_at__gte=target,
            reported_at__lt=next_month
        ).count()
        monthly_counts.append({
            'label': target.strftime('%b'),
            'count': count,
            'is_current': (i == 0),
        })

    context['monthly_counts'] = monthly_counts
    max_count = max((m['count'] for m in monthly_counts), default=1)
    context['monthly_max'] = max_count if max_count > 0 else 1

    # 7. INNE DANE
    global_announcement = Notification.objects.filter(is_global=True, is_active=True).exclude(read_by=request.user).order_by('-created_at').first()
    context['global_announcement'] = global_announcement

    conflict_qs = MonthlyConfirmation.objects.filter(status__in=['KONFLIKT', 'OCZEKUJE'])
    if not request.user.is_staff and not request.user.is_superuser:
        conflict_qs = conflict_qs.filter(mpk_number__in=allowed_mpk_ids)
    context['conflict_count'] = conflict_qs.count()

    context['active_pickups_count'] = Pickup.objects.filter(
        reporter=request.user,
        created_at__gte=first_day_month
    ).count()

    last_import = DataTransferLog.objects.filter(action='IMPORT').order_by('-created_at').first()
    context['last_import_date'] = last_import.created_at if last_import else None

    last_log = DataTransferLog.objects.order_by('-created_at').first()
    context['system_healthy'] = last_log.status != 'ERROR' if last_log else True

    return render(request, 'core/home.html', context)

@staff_member_required
def export_auditlog_view(request):
    date_from = request.GET.get('date_from', '').strip() or None
    date_to = request.GET.get('date_to', '').strip() or None
    user_id = request.GET.get('user_id', '').strip() or None
    content_type_id = request.GET.get('content_type_id', '').strip() or None

    df = generate_auditlog_export(
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        content_type_id=content_type_id
    )

    if df.empty:
        messages.warning(request, "Brak danych dla wybranych filtrów.")
        return redirect('core:admin_tasks')

    file_name = f"historia_zmian_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Historia Zmian')
        # workbook = writer.book
        worksheet = writer.sheets['Historia Zmian']

        # Formatting headers
        from openpyxl.styles import Font, Alignment
        header_font = Font(bold=True)
        for cell in worksheet[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Formatting data
        for row in worksheet.iter_rows(min_row=2, max_col=6, max_row=worksheet.max_row):
            for i, cell in enumerate(row):
                if i == 5: # Zmiany (JSON)
                    cell.alignment = Alignment(wrapText=True, vertical='top')
                else:
                    cell.alignment = Alignment(vertical='top')

        # Adjust column widths
        worksheet.column_dimensions['A'].width = 20 # Data zmiany
        worksheet.column_dimensions['B'].width = 30 # Użytkownik
        worksheet.column_dimensions['C'].width = 15 # Rodzaj akcji
        worksheet.column_dimensions['D'].width = 20 # Tabela
        worksheet.column_dimensions['E'].width = 30 # Obiekt
        worksheet.column_dimensions['F'].width = 50 # Zmiany (JSON)

    # Rejestracja w DataTransferLog
    try:
        DataTransferLog.objects.create(
            action='EXPORT',
            table_name="Historia Zmian (Auditlog)",
            file_name=f"{file_name}.xlsx",
            records_count=len(df),
            status='SUCCESS',
            created_by=request.user
        )
    except Exception:
        pass # Ignorujemy błędy przy zapisywaniu logu transferu

    return response

@staff_member_required
def create_global_announcement_view(request):
    if request.method == 'POST':
        form = GlobalAnnouncementForm(request.POST)
        if form.is_valid():
            # Usunięto: deaktywację poprzednich — wiele może być aktywnych jednocześnie
            announcement = form.save(commit=False)
            announcement.is_global = True
            announcement.is_active = True
            announcement.user = request.user
            announcement.save()
            messages.success(request, "Ogłoszenie globalne zostało opublikowane.")
        else:
            messages.error(request, "Błąd w formularzu ogłoszenia.")
    return redirect('core:admin_tasks')


@staff_member_required
def disable_global_announcement_view(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')  # przekazujemy pk konkretnego ogłoszenia
        if pk:
            Notification.objects.filter(pk=pk, is_global=True).update(is_active=False)
            messages.success(request, "Ogłoszenie zostało wyłączone.")
        else:
            # fallback: wyłącz wszystkie aktywne
            Notification.objects.filter(is_global=True, is_active=True).update(is_active=False)
            messages.success(request, "Wszystkie ogłoszenia zostały wyłączone.")
    return redirect('core:admin_tasks')
