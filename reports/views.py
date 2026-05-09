#reports/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from pickups.models import PickupWasteBin
from users.models import Permission
from waste.models import WasteFraction
from .models import MonthlyConfirmation, MonthlyConfirmationBin, SummaryCollectionSchedule
from .forms import ReportFilterForm
from .services import import_collection_data
import datetime
from django.contrib.admin.views.decorators import staff_member_required

def _odmien_rekord(n):
    if n == 1:
        return "1 rekord"
    elif 2 <= n <= 4:
        return f"{n} rekordy"
    else:
        return f"{n} rekordów"
    
@staff_member_required
def import_excel_view(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.csv')):
            messages.error(request, 'Nieprawidłowy format pliku. Proszę wgrać plik .xlsx lub .csv')
            return redirect('reports:monthly_summary')

        try:
            results = import_collection_data(excel_file, request.user)

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
                for error in results['errors'][:5]:  # Pokaż maksymalnie 5 pierwszych błędów
                    messages.error(request, error)
                if len(results['errors']) > 5:
                    messages.error(request, f"...oraz {len(results['errors']) - 5} innych błędów.")

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas importu: {str(e)}")

    return redirect('reports:monthly_summary')

@staff_member_required
def approve_confirmation(request, pk):
    confirmation = get_object_or_404(MonthlyConfirmation, pk=pk)
    
    if confirmation.status != 'ZATWIERDZONE':
        confirmation.status = 'ZATWIERDZONE'
        confirmation.approved_by = request.user
        confirmation.approved_at = timezone.now()
        confirmation.save()
        messages.success(request, f"Raport dla MPK {confirmation.mpk_number} został ostatecznie zatwierdzony.")
    else:
        messages.warning(request, "Ten raport jest już zatwierdzony.")

    return redirect(reverse('reports:monthly_summary') + f"?month={confirmation.month.month}&year={confirmation.month.year}")

@login_required
def monthly_summary_view(request):
    today = timezone.now().date()
    
    form = ReportFilterForm(request.GET or {'month': today.month, 'year': today.year}, user=request.user)

    selected_month = today.month
    selected_year = today.year
    selected_mpk = None

    if form.is_valid():
        selected_month = int(form.cleaned_data.get('month') or today.month)
        selected_year = int(form.cleaned_data.get('year') or today.year)
        selected_mpk = form.cleaned_data.get('mpk')

    query_filters = {'year': selected_year, 'month': selected_month}
    
    if not request.user.is_superuser:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, active=True
        ).values_list('mpk_number_id', flat=True)
        query_filters['mpk_number_id__in'] = allowed_mpk_ids

    if selected_mpk:
        query_filters['mpk_number_id'] = selected_mpk

    records = SummaryCollectionSchedule.objects.filter(**query_filters).select_related(
        'waste_fraction', 'mpk_number', 'waste_fraction__fraction_type'
    )

    first_day_month = datetime.date(selected_year, selected_month, 1)
    confirmations = MonthlyConfirmation.objects.filter(
        month=first_day_month
    ).values('mpk_number_id', 'status')
    
    status_map = {c['mpk_number_id']: c['status'] for c in confirmations}

    grouped_data = {}
    
    for record in records:
        mpk_obj = record.mpk_number
        mpk_name = str(mpk_obj.mpk_number)

        if mpk_name not in grouped_data:
            grouped_data[mpk_name] = {
                'mpk_id': mpk_obj.id,
                'status': status_map.get(mpk_obj.id, 'OCZEKUJE'), # Pobieramy status z mapy
                'fractions': {}
            }

        wf = record.waste_fraction
        name = wf.fraction_type.name if wf.fraction_type else "Inne"
        capacity = getattr(wf, 'capacity', '')
        capacity_str = f"{capacity}L" if capacity else ""
        group_key = f"{name}_{capacity}"

        if group_key not in grouped_data[mpk_name]['fractions']:
            lower_name = name.lower()
            if 'zmieszane' in lower_name: icon, color = 'bi-trash3-fill', 'secondary'
            elif any(x in lower_name for x in ['plastik', 'metal', 'tworzywa']): icon, color = 'bi-recycle', 'warning'
            elif any(x in lower_name for x in ['papier', 'makulatura']): icon, color = 'bi-box-seam', 'primary'
            elif 'szk' in lower_name: icon, color = 'bi-cup-straw', 'success'
            elif 'bio' in lower_name: icon, color = 'bi-tree-fill', 'success'
            else: icon, color = 'bi-trash', 'dark'

            grouped_data[mpk_name]['fractions'][group_key] = {
                'name': name,
                'capacity': capacity_str,
                'total_collected': 0,
                'icon': icon,
                'color': color
            }

        grouped_data[mpk_name]['fractions'][group_key]['total_collected'] += record.quantity

    final_grouped_data = []
    for mpk_name, data in grouped_data.items():
        fractions_list = list(data['fractions'].values())
        fractions_list.sort(key=lambda x: (x['name'], x['capacity']))
        
        final_grouped_data.append({
            'mpk_name': mpk_name,
            'mpk_id': data['mpk_id'],
            'status': data['status'],
            'fractions': fractions_list
        })
        
    final_grouped_data.sort(key=lambda x: x['mpk_name'])

    return render(request, 'reports/monthly_summary.html', {
        'form': form,
        'grouped_data': final_grouped_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
    })


@login_required
def verification_view(request):
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    mpk_id = request.GET.get('mpk')
    
    first_day = datetime.date(year, month, 1)
    
    if not mpk_id:
        return render(request, 'reports/verification_form.html', {'no_mpk': True})

    confirmation, created = MonthlyConfirmation.objects.get_or_create(
        mpk_number_id=mpk_id,
        month=first_day
    )

    pickups = PickupWasteBin.objects.filter(
        pickup__mpk_number_id=mpk_id,
        pickup__reported_at__month=month,
        pickup__reported_at__year=year
    ).values('waste_fraction_id').annotate(total=Sum('quantity'))
    
    imports = SummaryCollectionSchedule.objects.filter(
        mpk_number_id=mpk_id,
        month=month,
        year=year
    ).values('waste_fraction_id').annotate(total=Sum('quantity'))

    saved_bins = {b.waste_fraction_id: b for b in confirmation.bins.all()}
    all_fraction_ids = set([p['waste_fraction_id'] for p in pickups] + [i['waste_fraction_id'] for i in imports])
    fractions = WasteFraction.objects.filter(id__in=all_fraction_ids).select_related('fraction_type')

    comparison_data = []
    for f in fractions:
        reported = next((p['total'] for p in pickups if p['waste_fraction_id'] == f.id), 0)
        collected = next((i['total'] for i in imports if i['waste_fraction_id'] == f.id), 0)
        saved = saved_bins.get(f.id)
        
        comparison_data.append({
            'fraction': f,
            'reported_qty': int(reported),
            'collected_qty': int(collected),
            'confirmed_qty': int(saved.confirmed_quantity) if saved else int(collected),
            'note': saved.note if saved else "",
            'is_conflict': reported != collected
        })

    if request.method == 'POST':
        decision = request.POST.get('decision_status')
        has_error = False
        temp_data = []

        # 1. Walidacja danych wejściowych
        diff_found = False
        for f in fractions:
            reported_in_system = next((p['total'] for p in pickups if p['waste_fraction_id'] == f.id), 0)
            collected_from_excel = next((i['total'] for i in imports if i['waste_fraction_id'] == f.id), 0)
            
            qty_input = request.POST.get(f'qty_{f.id}')
            note_input = request.POST.get(f'note_{f.id}', "").strip()

            if qty_input is not None:
                qty_confirmed = int(qty_input)
                
                # Sprawdzamy czy użytkownik zmienił wartość względem tego co podał dostawca w Excelu
                if qty_confirmed != int(collected_from_excel):
                    diff_found = True
                    if not note_input:
                        messages.error(request, f"Dla frakcji {f} wymagana jest uwaga przy rozbieżności!")
                        has_error = True
                
                temp_data.append({
                    'fraction': f,
                    'qty': qty_confirmed,
                    'note': note_input
                })

        if decision == 'KONFLIKT' and not diff_found:
            messages.error(request, "Wybrano status 'Występują rozbieżności', ale nie zmieniono żadnej ilości względem danych dostawcy!")
            has_error = True

        if not has_error:
            existing_bins = {
                b.waste_fraction_id: b
                for b in MonthlyConfirmationBin.objects.filter(confirmation=confirmation)
            }
            to_create = []
            to_update = []

            for item in temp_data:
                fraction_id = item['fraction'].id
                if fraction_id in existing_bins:
                    bin_obj = existing_bins[fraction_id]
                    if bin_obj.confirmed_quantity != item['qty'] or bin_obj.note != item['note']:
                        bin_obj.confirmed_quantity = item['qty']
                        bin_obj.note = item['note']
                        to_update.append(bin_obj)
                else:
                    to_create.append(
                        MonthlyConfirmationBin(
                            confirmation=confirmation,
                            waste_fraction=item['fraction'],
                            confirmed_quantity=item['qty'],
                            note=item['note']
                        )
                    )

            if to_create:
                MonthlyConfirmationBin.objects.bulk_create(to_create)
            if to_update:
                MonthlyConfirmationBin.objects.bulk_update(to_update, ['confirmed_quantity', 'note'])

            if not confirmation.created_by:
                confirmation.created_by = request.user
            confirmation.updated_by = request.user
            confirmation.status = decision
            confirmation.approved_by = request.user
            confirmation.approved_at = timezone.now()
            confirmation.save()
            
            messages.success(request, "Weryfikacja została zapisana pomyślnie.")
            return redirect('reports:monthly_summary')

    return render(request, 'reports/verification_form.html', {
        'confirmation': confirmation,
        'comparison_data': comparison_data,
        'month': month,
        'year': year
    })