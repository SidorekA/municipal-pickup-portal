import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import pandas as pd
from datetime import date, timedelta
from django.db import transaction
from collections import defaultdict

from reports.services import import_collection_data
from scheduling.services import get_next_pickup_date
from reports.models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from waste.models import WasteFraction, WasteFractionType
from locations.models import MPKNumber, Location
from pickups.models import Pickup, PickupWasteBin

def precalculate_system_sums(df):
    """
    Precalculate system sums for all unique (mpk_number, fraction_name, capacity, month, year) combinations in the dataframe.
    """
    unique_combinations = df[['Numer MPK', 'Frakcja', 'Pojemność', 'Miesiąc', 'Rok']].drop_duplicates()

    # Bulk fetch MPKs
    mpk_numbers = unique_combinations['Numer MPK'].unique()
    mpks = {mpk.mpk_number: mpk for mpk in MPKNumber.objects.filter(mpk_number__in=mpk_numbers)}

    # Bulk fetch Fractions
    fraction_pairs = unique_combinations[['Frakcja', 'Pojemność']].drop_duplicates()
    fractions_q = WasteFraction.objects.none()
    for _, row in fraction_pairs.iterrows():
        fractions_q |= WasteFraction.objects.filter(fraction_type__name=row['Frakcja'], capacity=row['Pojemność'])

    fractions = {(f.fraction_type.name, f.capacity): f for f in fractions_q.select_related('fraction_type').prefetch_related('fraction_type__schedules')}

    # Pre-calculate ranges
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
        ranges.append({'month': m, 'year': y, 'start': start_search, 'end': end_search})

    system_sums = defaultdict(int)

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

        # Optimization: fetch pickups in bulk per mpk, fraction and range
        pickups = PickupWasteBin.objects.filter(
            pickup__mpk_number=mpk,
            waste_fraction=fraction,
            pickup__reported_at__date__range=[range_info['start'], range_info['end']]
        ).select_related('pickup')

        total_qty = 0
        for p in pickups:
            planned_date = get_next_pickup_date(
                fraction.fraction_type,
                submitted_at=p.pickup.reported_at
            )

            if planned_date and planned_date.month == month and planned_date.year == year:
                total_qty += p.quantity

        system_sums[(mpk.id, fraction.id, month, year)] = total_qty

    return mpks, fractions, system_sums
