#reports/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from users.models import Permission
from .models import SummaryCollectionSchedule
from .forms import ReportFilterForm

@login_required
def monthly_summary_view(request):
    today = timezone.now().date()
    
    # Przekazujemy request.user do formularza
    form = ReportFilterForm(request.GET or {'month': today.month, 'year': today.year}, user=request.user)

    selected_month = today.month
    selected_year = today.year
    selected_mpk = None

    if form.is_valid():
        selected_month = int(form.cleaned_data.get('month') or today.month)
        selected_year = int(form.cleaned_data.get('year') or today.year)
        selected_mpk = form.cleaned_data.get('mpk')

    if request.user.is_superuser:
        records = SummaryCollectionSchedule.objects.filter(
            year=selected_year,
            month=selected_month
        ).select_related('waste_fraction', 'mpk_number')
    else:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, 
            active=True
        ).values_list('mpk_number_id', flat=True)

        records = SummaryCollectionSchedule.objects.filter(
            mpk_number_id__in=allowed_mpk_ids,
            year=selected_year,
            month=selected_month
        ).select_related('waste_fraction', 'mpk_number')

    if selected_mpk:
        records = records.filter(mpk_number_id=selected_mpk)

    # Zmieniona logika - grupujemy po MPK
    grouped_data = {}
    
    for record in records:
        mpk_name = str(record.mpk_number.mpk_number)

        if mpk_name not in grouped_data:
            grouped_data[mpk_name] = {}

        wf = record.waste_fraction

        try:
            name = wf.fraction_type.name
        except AttributeError:
            name = getattr(wf, 'code', str(wf))
            
        capacity = getattr(wf, 'capacity', '')
        capacity_str = f"{capacity}L" if capacity else ""
        group_key = f"{name}_{capacity}"

        if group_key not in grouped_data[mpk_name]:
            lower_name = name.lower()
            if 'zmieszane' in lower_name:
                icon, color = 'bi-trash3-fill', 'secondary'
            elif 'plastik' in lower_name or 'metal' in lower_name or 'tworzywa' in lower_name:
                icon, color = 'bi-recycle', 'warning'
            elif 'papier' in lower_name or 'makulatura' in lower_name:
                icon, color = 'bi-box-seam', 'primary'
            elif 'szkło' in lower_name or 'szklo' in lower_name:
                icon, color = 'bi-cup-straw', 'success'
            elif 'bio' in lower_name:
                icon, color = 'bi-tree-fill', 'success'
            else:
                icon, color = 'bi-trash', 'dark'

            grouped_data[mpk_name][group_key] = {
                'name': name,
                'capacity': capacity_str,
                'total_collected': 0,
                'icon': icon,
                'color': color
            }

        grouped_data[mpk_name][group_key]['total_collected'] += record.quantity

    # Przekształcamy słownik w listę dla łatwego iterowania w HTML
    final_grouped_data = []
    for mpk_name, fractions_dict in grouped_data.items():
        fractions_list = list(fractions_dict.values())
        fractions_list.sort(key=lambda x: (x['name'], x['capacity']))
        final_grouped_data.append({
            'mpk_name': mpk_name,
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