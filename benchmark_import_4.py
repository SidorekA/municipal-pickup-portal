import os
import django
import time
import cProfile
import pstats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import pandas as pd
from reports.services import import_collection_data
from django.contrib.auth import get_user_model
from locations.models import MPKNumber, Location
from waste.models import WasteFraction, WasteFractionType
from reports.models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from pickups.models import Pickup, PickupWasteBin

User = get_user_model()

def setup_data():
    user, _ = User.objects.get_or_create(username='testuser', email='test@test.com')
    frac_type, _ = WasteFractionType.objects.get_or_create(name='Test', code=99)
    frac, _ = WasteFraction.objects.get_or_create(fraction_type=frac_type, capacity=120)

    mpks = []
    # Create 200 mpks
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    for m in range(200):
        mpk, _ = MPKNumber.objects.get_or_create(mpk_number=2000+m)
        mpks.append(mpk)
        loc, _ = Location.objects.get_or_create(
            mpk_number=mpk,
            obj_name=f'Test Loc {m}',
            org_unit_name='Test Unit',
            localization='Test Localization'
        )
        # 10 pickups per MPK
        for i in range(10):
            p = Pickup.objects.create(
                pickup_number=f'ZGL-{2000+m}-{i}',
                location=loc,
                mpk_number=mpk,
                reporter=user,
            )
            p.reported_at = datetime(2023, 5, 15, 10, 0, tzinfo=ZoneInfo("Europe/Warsaw")) - timedelta(days=i)
            p.save()
            PickupWasteBin.objects.create(pickup=p, waste_fraction=frac, quantity=1)

    return user, mpks, frac

def create_test_csv():
    data = []
    for m in range(200):
        data.append({
            'Numer MPK': 2000+m,
            'Frakcja': 'Test',
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': '2023-05-10'
        })
    df = pd.DataFrame(data)
    df.to_csv('test_import.csv', index=False)

def run_benchmark():
    print("Setting up data...")
    user, mpks, frac = setup_data()
    create_test_csv()

    # clear previous data
    SummaryCollectionSchedule.objects.all().delete()
    MonthlyConfirmation.objects.all().delete()
    MonthlyConfirmationBin.objects.all().delete()

    print("Starting import...")
    import django.db
    django.db.reset_queries()

    start = time.time()
    results = import_collection_data('test_import.csv', user)
    end = time.time()

    print(f"Import results: {results}")
    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Number of queries: {len(django.db.connection.queries)}")

if __name__ == '__main__':
    run_benchmark()
