#reports/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from pickups.models import PickupWasteBin
from users.models import Permission
from waste.models import WasteFraction
from .models import MonthlyConfirmation, MonthlyConfirmationBin, SummaryCollectionSchedule
from .forms import ReportFilterForm
import datetime

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

    # Pobieranie rekordów
    if request.user.is_superuser:
        records = SummaryCollectionSchedule.objects.filter(
            year=selected_year,
            month=selected_month
        ).select_related('waste_fraction', 'mpk_number', 'waste_fraction__fraction_type')
    else:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, 
            active=True
        ).values_list('mpk_number_id', flat=True)

        records = SummaryCollectionSchedule.objects.filter(
            mpk_number_id__in=allowed_mpk_ids,
            year=selected_year,
            month=selected_month
        ).select_related('waste_fraction', 'mpk_number', 'waste_fraction__fraction_type')

    if selected_mpk:
        records = records.filter(mpk_number_id=selected_mpk)

    # Logika grupowania
    grouped_data = {}
    
    for record in records:
        mpk_obj = record.mpk_number
        mpk_name = str(mpk_obj.mpk_number)

        if mpk_name not in grouped_data:
            grouped_data[mpk_name] = {
                'mpk_id': mpk_obj.id,
                'fractions': {}
            }

        wf = record.waste_fraction
        try:
            name = wf.fraction_type.name
        except AttributeError:
            name = "Nieznana frakcja"
            
        capacity = getattr(wf, 'capacity', '')
        capacity_str = f"{capacity}L" if capacity else ""
        group_key = f"{name}_{capacity}"

        if group_key not in grouped_data[mpk_name]['fractions']:
            lower_name = name.lower()
            # Logika kolorów i ikon
            if 'zmieszane' in lower_name:
                icon, color = 'bi-trash3-fill', 'secondary'
            elif any(x in lower_name for x in ['plastik', 'metal', 'tworzywa']):
                icon, color = 'bi-recycle', 'warning'
            elif any(x in lower_name for x in ['papier', 'makulatura']):
                icon, color = 'bi-box-seam', 'primary'
            elif 'szk' in lower_name: # szkło / szklo
                icon, color = 'bi-cup-straw', 'success'
            elif 'bio' in lower_name:
                icon, color = 'bi-tree-fill', 'success'
            else:
                icon, color = 'bi-trash', 'dark'

            grouped_data[mpk_name]['fractions'][group_key] = {
                'name': name,
                'capacity': capacity_str,
                'total_collected': 0,
                'icon': icon,
                'color': color
            }

        grouped_data[mpk_name]['fractions'][group_key]['total_collected'] += record.quantity

    # Przygotowanie danych do template (final_grouped_data)
    final_grouped_data = []
    for mpk_name, data in grouped_data.items():
        # Sortujemy listę słowników znajdującą się pod kluczem 'fractions'
        fractions_list = list(data['fractions'].values())
        fractions_list.sort(key=lambda x: (x['name'], x['capacity']))
        
        final_grouped_data.append({
            'mpk_name': mpk_name,
            'mpk_id': data['mpk_id'],
            'fractions': fractions_list
        })
        
    final_grouped_data.sort(key=lambda x: x['mpk_name'])

    context = {
        'form': form,
        'grouped_data': final_grouped_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }
    
    return render(request, 'reports/monthly_summary.html', context)


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
            'reported_qty': reported,
            'collected_qty': collected,
            'confirmed_qty': saved.confirmed_quantity if saved else collected,
            'note': saved.note if saved else "",
            'is_conflict': reported != collected
        })

    if request.method == 'POST':
        for f in fractions:
            qty = request.POST.get(f'qty_{f.id}')
            note = request.POST.get(f'note_{f.id}')
            if qty is not None:
                MonthlyConfirmationBin.objects.update_or_create(
                    confirmation=confirmation,
                    waste_fraction=f,
                    defaults={'confirmed_quantity': qty, 'note': note}
                )
        
        confirmation.status = 'POTWIERDZONE'
        confirmation.confirmed_by = request.user
        confirmation.confirmed_at = timezone.now()
        confirmation.save()
        messages.success(request, "Zestawienie zostało potwierdzone.")
        return redirect('reports:monthly_summary')

    return render(request, 'reports/verification_form.html', {
        'confirmation': confirmation,
        'comparison_data': comparison_data,
        'month': month,
        'year': year
    })