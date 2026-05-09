# reports/services.py

import pandas as pd
from datetime import date, timedelta
from collections import defaultdict
from django.db import transaction
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


def precalculate_system_sums(df):
    """
    Precalculate system sums for all unique combinations in the dataframe.
    """
    valid_rows = []
    for _, row in df.iterrows():
        try:
            valid_rows.append({
                'Numer MPK': int(row['Numer MPK']),
                'Frakcja': row['Frakcja'],
                'Pojemność': int(row['Pojemność']),
                'Miesiąc': int(row['Miesiąc']),
                'Rok': int(row['Rok'])
            })
        except (ValueError, TypeError):
            continue

    if not valid_rows:
        return {}, {}, defaultdict(int)

    valid_df = pd.DataFrame(valid_rows)
    unique_combinations = valid_df.drop_duplicates()

    mpk_numbers = unique_combinations['Numer MPK'].unique()
    mpks = {mpk.mpk_number: mpk for mpk in MPKNumber.objects.filter(mpk_number__in=mpk_numbers)}

    fraction_pairs = unique_combinations[['Frakcja', 'Pojemność']].drop_duplicates()
    fractions_q = WasteFraction.objects.none()
    for _, row in fraction_pairs.iterrows():
        fractions_q |= WasteFraction.objects.filter(fraction_type__name=row['Frakcja'], capacity=row['Pojemność'])

    fractions = {(f.fraction_type.name, f.capacity): f for f in fractions_q.select_related('fraction_type').prefetch_related('fraction_type__schedules')}

    min_date = None
    max_date = None

    ranges = []
    month_years = unique_combinations[['Miesiąc', 'Rok']].drop_duplicates()
    for _, row in month_years.iterrows():
        m, y = int(row['Miesiąc']), int(row['Rok'])
        first_day_current = date(y, m, 1)
        if m == 12:
            first_day_next = date(y + 1, 1, 1)
        else:
            first_day_next = date(y, m + 1, 1)

        start_search = first_day_current - timedelta(days=10)
        end_search = first_day_next + timedelta(days=5)

        if min_date is None or start_search < min_date:
            min_date = start_search
        if max_date is None or end_search > max_date:
            max_date = end_search

        ranges.append({'month': m, 'year': y, 'start': start_search, 'end': end_search})

    system_sums = defaultdict(int)

    if min_date is not None and max_date is not None and mpk_numbers.size > 0:
        all_pickups = PickupWasteBin.objects.filter(
            pickup__mpk_number__mpk_number__in=mpk_numbers,
            pickup__reported_at__date__range=[min_date, max_date]
        ).select_related('pickup', 'waste_fraction', 'pickup__mpk_number')

        pickups_by_mpk_frac = defaultdict(list)
        for p in all_pickups:
            key = (p.pickup.mpk_number_id, p.waste_fraction_id)
            pickups_by_mpk_frac[key].append(p)

        for _, row in unique_combinations.iterrows():
            mpk_num = int(row['Numer MPK'])
            f_name = row['Frakcja']
            f_cap = int(row['Pojemność'])
            month = int(row['Miesiąc'])
            year = int(row['Rok'])

            mpk = mpks.get(mpk_num)
            fraction = fractions.get((f_name, f_cap))

            if not mpk or not fraction:
                continue

            range_info = next((r for r in ranges if r['month'] == month and r['year'] == year), None)
            if not range_info:
                continue

            relevant_pickups = pickups_by_mpk_frac.get((mpk.id, fraction.id), [])

            total_qty = 0
            for p in relevant_pickups:
                # filter by range specific to this month/year combo
                if not (range_info['start'] <= p.pickup.reported_at.date() <= range_info['end']):
                    continue

                planned_date = get_next_pickup_date(
                    fraction.fraction_type,
                    submitted_at=p.pickup.reported_at
                )

                if planned_date and planned_date.month == month and planned_date.year == year:
                    total_qty += p.quantity

            system_sums[(mpk.id, fraction.id, month, year)] = total_qty

    return mpks, fractions, system_sums

def import_collection_data(file_path, user):
    if str(file_path).endswith('.csv') or hasattr(file_path, 'name') and file_path.name.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, parse_dates=['Data Odbioru'])

    results = {'imported': 0, 'skipped': 0, 'auto_confirmed': 0, 'errors': []}

    mpks, fractions, system_sums = precalculate_system_sums(df)

    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                mpk_num = int(row['Numer MPK'])
                f_name = row['Frakcja']
                f_cap = int(row['Pojemność'])

                mpk = mpks.get(mpk_num)
                if not mpk:
                    mpk = MPKNumber.objects.get(mpk_number=mpk_num)

                fraction = fractions.get((f_name, f_cap))
                if not fraction:
                    fraction = WasteFraction.objects.get(
                        fraction_type__name=f_name,
                        capacity=f_cap
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
                    system_qty = system_sums.get((mpk.id, fraction.id, month, year), 0)
                    # Fallback if not precalculated for some reason
                    if (mpk.id, fraction.id, month, year) not in system_sums:
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