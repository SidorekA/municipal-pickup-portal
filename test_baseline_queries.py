import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import pandas as pd
from django.contrib.auth import get_user_model
from locations.models import MPKNumber, Location
from waste.models import WasteFraction, WasteFractionType
from reports.models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from pickups.models import Pickup, PickupWasteBin

User = get_user_model()

def run_benchmark():
    user = User.objects.get(username='testuser')
    # Use the old code for comparison
    from datetime import date, timedelta
    from django.db import transaction
    from scheduling.services import get_next_pickup_date

    def get_system_sum_for_month(mpk, fraction, month, year):
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

    def old_import_collection_data(file_path, user):
        df = pd.read_csv(file_path)
        results = {'imported': 0, 'skipped': 0, 'auto_confirmed': 0, 'errors': []}

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    mpk = MPKNumber.objects.get(mpk_number=int(row['Numer MPK']))
                    fraction = WasteFraction.objects.get(
                        fraction_type__name=row['Frakcja'],
                        capacity=int(row['Pojemność'])
                    )

                    excel_qty = int(row['Ilość'])
                    month = int(row['Miesiąc'])
                    year = int(row['Rok'])

                    raw_date = row['Data Odbioru']
                    if pd.isna(raw_date):
                        date_summary = date(year, month, 1)
                    else:
                        date_summary = pd.to_datetime(raw_date).date()

                    obj, created = SummaryCollectionSchedule.objects.update_or_create(
                        mpk_number=mpk,
                        year=year,
                        month=month,
                        waste_fraction=fraction,
                        defaults={
                            'quantity': excel_qty,
                            'imported_by': user,
                            'date_summary': date_summary,
                        }
                    )
                    if created:
                        results['imported'] += 1
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
                    else:
                        results['skipped'] += 1

                except Exception as e:
                    results['errors'].append(f"Błąd w wierszu {index}: {str(e)}")

        return results

    SummaryCollectionSchedule.objects.all().delete()
    MonthlyConfirmation.objects.all().delete()
    MonthlyConfirmationBin.objects.all().delete()

    import django.db
    django.db.reset_queries()

    start = time.time()
    results = old_import_collection_data('test_import.csv', user)
    end = time.time()

    print(f"Import results: {results}")
    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Number of queries: {len(django.db.connection.queries)}")

if __name__ == '__main__':
    run_benchmark()
