import os
import django
import time

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
    mpk, _ = MPKNumber.objects.get_or_create(mpk_number=12345)
    frac_type, _ = WasteFractionType.objects.get_or_create(name='Test', code=99)
    frac, _ = WasteFraction.objects.get_or_create(fraction_type=frac_type, capacity=120)

    # Create some pickups
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    loc, _ = Location.objects.get_or_create(
        mpk_number=mpk,
        obj_name='Test Loc',
        org_unit_name='Test Unit',
        localization='Test Localization'
    )
    # create more pickups to make the system sum query more visible
    for i in range(100):
        p = Pickup.objects.create(
            pickup_number=f'ZGL-12345-{i}',
            location=loc,
            mpk_number=mpk,
            reporter=user,
        )
        p.reported_at = datetime(2023, 5, 15, 10, 0, tzinfo=ZoneInfo("Europe/Warsaw")) - timedelta(days=i)
        p.save()
        PickupWasteBin.objects.create(pickup=p, waste_fraction=frac, quantity=1)

    return user, mpk, frac

def create_test_csv():
    data = []
    # Create enough rows so the repeated query becomes a bottleneck
    for i in range(500):
        data.append({
            'Numer MPK': 12345,
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
    user, mpk, frac = setup_data()
    create_test_csv()

    # clear previous data
    SummaryCollectionSchedule.objects.all().delete()
    MonthlyConfirmation.objects.all().delete()
    MonthlyConfirmationBin.objects.all().delete()

    start = time.time()
    results = import_collection_data('test_import.csv', user)
    end = time.time()

    print(f"Import results: {results}")
    print(f"Time taken: {end - start:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
