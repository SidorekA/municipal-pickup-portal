# reports/services.py

import pandas as pd
from datetime import date
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from waste.models import WasteFraction
from locations.models import MPKNumber
from pickups.models import PickupWasteBin

def import_collection_data(file_path, user):
    """
    Importuje dane z Excela/CSV i automatycznie weryfikuje zgodność z systemem.
    """
    df = pd.read_csv(file_path) if str(file_path).endswith('.csv') else pd.read_excel(file_path)
    
    summary_results = {
        'imported': 0,
        'auto_confirmed': 0,
        'errors': []
    }

    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                mpk = MPKNumber.objects.get(mpk_number=str(row['Numer MPK']))
                
                fraction = WasteFraction.objects.get(
                    fraction_type__name=row['Frakcja'],
                    capacity=int(row['Pojemność'])
                )

                schedule, _ = SummaryCollectionSchedule.objects.update_or_create(
                    mpk_number=mpk,
                    year=int(row['Rok']),
                    month=int(row['Miesiąc']),
                    waste_fraction=fraction,
                    defaults={
                        'quantity': int(row['Ilość']),
                        'date_summary': row['Data zestawienia'],
                        'imported_by': user
                    }
                )
                summary_results['imported'] += 1

                first_day = date(int(row['Rok']), int(row['Miesiąc']), 1)
                confirmation, _ = MonthlyConfirmation.objects.get_or_create(
                    mpk_number=mpk,
                    month=first_day
                )

                system_qty = PickupWasteBin.objects.filter(
                    pickup__mpk_number=mpk,
                    pickup__reported_at__month=row['Miesiąc'],
                    pickup__reported_at__year=row['Rok'],
                    waste_fraction=fraction
                ).aggregate(total=Sum('quantity'))['total'] or 0

                if int(system_qty) == int(row['Ilość']):
                    MonthlyConfirmationBin.objects.update_or_create(
                        confirmation=confirmation,
                        waste_fraction=fraction,
                        defaults={
                            'confirmed_quantity': int(row['Ilość']),
                            'note': 'Automatyczna weryfikacja: zgodność z systemem.'
                        }
                    )
                    
                    confirmation.status = 'POTWIERDZONE'
                    confirmation.updated_by = user
                    confirmation.save()
                    summary_results['auto_confirmed'] += 1

            except MPKNumber.DoesNotExist:
                summary_results['errors'].append(f"Wiersz {index+2}: MPK {row['Numer MPK']} nie istnieje.")
            except WasteFraction.DoesNotExist:
                summary_results['errors'].append(f"Wiersz {index+2}: Frakcja {row['Frakcja']} {row['Pojemność']}L nie istnieje.")
            except Exception as e:
                summary_results['errors'].append(f"Wiersz {index+2}: Błąd krytyczny: {str(e)}")

    return summary_results