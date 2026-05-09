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
    frac_type, _ = WasteFractionType.objects.get_or_create(name='Test', code=99)
    frac, _ = WasteFraction.objects.get_or_create(fraction_type=frac_type, capacity=120)

    mpk, _ = MPKNumber.objects.get_or_create(mpk_number=12345)
    loc, _ = Location.objects.get_or_create(
        mpk_number=mpk,
        obj_name='Test Loc',
        org_unit_name='Test Unit',
        localization='Test Localization'
    )

    return user

def create_test_csv_with_errors():
    data = []
    # Valid row
    data.append({
        'Numer MPK': 12345,
        'Frakcja': 'Test',
        'Pojemność': 120,
        'Ilość': 1,
        'Miesiąc': 5,
        'Rok': 2023,
        'Data Odbioru': '2023-05-10'
    })
    # Empty row (what pandas gives as NaN)
    data.append({
        'Numer MPK': pd.NA,
        'Frakcja': pd.NA,
        'Pojemność': pd.NA,
        'Ilość': pd.NA,
        'Miesiąc': pd.NA,
        'Rok': pd.NA,
        'Data Odbioru': pd.NA
    })
    # Invalid data row
    data.append({
        'Numer MPK': 'bad',
        'Frakcja': 'Test',
        'Pojemność': 120,
        'Ilość': 1,
        'Miesiąc': 5,
        'Rok': 2023,
        'Data Odbioru': '2023-05-10'
    })

    df = pd.DataFrame(data)
    df.to_csv('test_import.csv', index=False)

def run_test():
    user = setup_data()
    create_test_csv_with_errors()

    results = import_collection_data('test_import.csv', user)
    print(f"Results: {results}")

if __name__ == '__main__':
    run_test()
