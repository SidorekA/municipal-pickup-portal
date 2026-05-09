# reports/services.py

import pandas as pd
from datetime import date, timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from scheduling.services import get_next_pickup_date
from .models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from waste.models import WasteFraction
from locations.models import MPKNumber
from pickups.models import PickupWasteBin


def get_system_sum_for_month(mpk, fraction, month, year):
    """
    Sumuje zgłoszenia, których PLANOWANY odbiór wypada w danym miesiącu.
    """
    first_day_current = date(year, month, 1)
    if month == 12:
        first_day_next = date(year + 1, 1, 1)
    else:
        first_day_next = date(year, month + 1, 1)
    
    start_search = first_day_current - timedelta(days=10)
    end_search = first_day_next + timedelta(days=5)

    pickups = PickupWasteBin.objects.filter(
        pickup__mpk_number=mpk,
        waste_fraction=fraction,
        pickup__reported_at__date__range=[start_search, end_search]
    ).select_related('pickup')

    total_qty = 0
    
    for p in pickups:
        planned_date = get_next_pickup_date(
            fraction.fraction_type, 
            submitted_at=p.pickup.reported_at
        )
        
        if planned_date and planned_date.month == month and planned_date.year == year:
            total_qty += p.quantity
            
    return total_qty

def import_collection_data(file_path, user):
    df = pd.read_excel(file_path)
    
    results = {'imported': 0, 'auto_confirmed': 0, 'errors': []}

    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                mpk = MPKNumber.objects.get(mpk_number=str(row['Numer MPK']))
                fraction = WasteFraction.objects.get(
                    fraction_type__name=row['Frakcja'],
                    capacity=int(row['Pojemność'])
                )
                
                excel_qty = int(row['Ilość'])
                month = int(row['Miesiąc'])
                year = int(row['Rok'])

                SummaryCollectionSchedule.objects.update_or_create(
                    mpk_number=mpk,
                    year=year,
                    month=month,
                    waste_fraction=fraction,
                    defaults={'quantity': excel_qty, 'imported_by': user}
                )

                system_qty = get_system_sum_for_month(mpk, fraction, month, year)

                if system_qty == excel_qty:
                    first_day = date(year, month, 1)
                    confirmation, _ = MonthlyConfirmation.objects.get_or_create(
                        mpk_number=mpk, month=first_day
                    )
                    
                    MonthlyConfirmationBin.objects.update_or_create(
                        confirmation=confirmation,
                        waste_fraction=fraction,
                        defaults={
                            'confirmed_quantity': excel_qty,
                            'note': 'Zgodność automatyczna (uwzględniono przesunięcia dat).'
                        }
                    )
                    confirmation.status = 'POTWIERDZONE'
                    confirmation.save()
                    results['auto_confirmed'] += 1
                
                results['imported'] += 1

            except Exception as e:
                results['errors'].append(f"Błąd w wierszu {index}: {str(e)}")

    return results