import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from datetime import date, timedelta
from django.db.models import Prefetch
from scheduling.services import get_next_pickup_date
from locations.models import MPKNumber
from waste.models import WasteFraction
from reports.models import SummaryCollectionSchedule
from pickups.models import PickupWasteBin

def prefetch_system_sums(df_records):
    # To prefetch all the necessary data:
    # 1. extract unique mpks, fractions, and year-months
    mpk_ids = set()
    fraction_ids = set()
    month_years = set()

    for row in df_records:
        mpk_ids.add(row['Numer MPK'])
        fraction_ids.add((row['Frakcja'], row['Pojemność']))
        month_years.add((row['Miesiąc'], row['Rok']))

    # Get mpks and fractions efficiently
    mpks_dict = {m.mpk_number: m for m in MPKNumber.objects.filter(mpk_number__in=mpk_ids)}

    fractions_q = WasteFraction.objects.none()
    for f_name, f_cap in fraction_ids:
        fractions_q |= WasteFraction.objects.filter(fraction_type__name=f_name, capacity=f_cap)

    fractions_list = list(fractions_q.select_related('fraction_type').prefetch_related('fraction_type__schedules'))
    fractions_dict = {(f.fraction_type.name, f.capacity): f for f in fractions_list}

    # Pre-calculate ranges
    ranges = []
    for m, y in month_years:
        first_day_current = date(y, m, 1)
        if m == 12:
            first_day_next = date(y + 1, 1, 1)
        else:
            first_day_next = date(y, m + 1, 1)

        start_search = first_day_current - timedelta(days=10)
        end_search = first_day_next + timedelta(days=5)
        ranges.append((m, y, start_search, end_search))

    print(f"Ranges: {ranges}")
