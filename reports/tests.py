from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from locations.models import MPKNumber, Location
from waste.models import WasteFractionType, WasteFraction
from scheduling.models import CollectionSchedule
from pickups.models import Pickup, PickupWasteBin

from .services import get_system_sum_for_month

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

class GetSystemSumForMonthTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')

        self.mpk = MPKNumber.objects.create(mpk_number=123)
        self.location = Location.objects.create(
            mpk_number=self.mpk,
            obj_name='Test Object',
            org_unit_name='Test Unit',
            localization='Test Loc'
        )

        self.fraction_type = WasteFractionType.objects.create(name='Test Fraction Type', code=101)
        self.fraction = WasteFraction.objects.create(fraction_type=self.fraction_type, capacity=120)

        CollectionSchedule.objects.create(fraction_type=self.fraction_type, day_of_week=1)
        CollectionSchedule.objects.create(fraction_type=self.fraction_type, day_of_week=4)
        CollectionSchedule.objects.create(fraction_type=self.fraction_type, day_of_week=5)

    def test_month_boundary(self):
        """
        Test that a pickup crossing the month boundary correctly attributes to the right month based on schedule.
        """
        # 1. Report on Wed Jan 30 11:00
        dt_jan = datetime(2019, 1, 30, 11, 0, tzinfo=WARSAW_TZ)
        with patch('django.utils.timezone.now', return_value=dt_jan):
            pickup_jan = Pickup.objects.create(
                location=self.location,
                mpk_number=self.mpk,
                reporter=self.user,
                status='NOWE',
            )
            PickupWasteBin.objects.create(pickup=pickup_jan, waste_fraction=self.fraction, quantity=10)
            Pickup.objects.filter(pk=pickup_jan.pk).update(reported_at=dt_jan)

        # 2. Report on Wed Jan 30 13:00
        dt_feb = datetime(2019, 1, 30, 13, 0, tzinfo=WARSAW_TZ)
        with patch('django.utils.timezone.now', return_value=dt_feb):
            pickup_feb = Pickup.objects.create(
                location=self.location,
                mpk_number=self.mpk,
                reporter=self.user,
                status='NOWE',
            )
            PickupWasteBin.objects.create(pickup=pickup_feb, waste_fraction=self.fraction, quantity=20)
            Pickup.objects.filter(pk=pickup_feb.pk).update(reported_at=dt_feb)

        dt_dec = datetime(2018, 12, 30, 11, 0, tzinfo=WARSAW_TZ)
        with patch('django.utils.timezone.now', return_value=dt_dec):
            pickup_dec = Pickup.objects.create(
                location=self.location,
                mpk_number=self.mpk,
                reporter=self.user,
                status='NOWE',
            )
            PickupWasteBin.objects.create(pickup=pickup_dec, waste_fraction=self.fraction, quantity=100)
            Pickup.objects.filter(pk=pickup_dec.pk).update(reported_at=dt_dec)

        dt_jan_next = datetime(2018, 12, 30, 13, 0, tzinfo=WARSAW_TZ)
        with patch('django.utils.timezone.now', return_value=dt_jan_next):
            pickup_jan_next = Pickup.objects.create(
                location=self.location,
                mpk_number=self.mpk,
                reporter=self.user,
                status='NOWE',
            )
            PickupWasteBin.objects.create(pickup=pickup_jan_next, waste_fraction=self.fraction, quantity=200)
            Pickup.objects.filter(pk=pickup_jan_next.pk).update(reported_at=dt_jan_next)

        sum_jan_2019 = get_system_sum_for_month(self.mpk, self.fraction, 1, 2019)
        self.assertEqual(sum_jan_2019, 210)

        sum_feb_2019 = get_system_sum_for_month(self.mpk, self.fraction, 2, 2019)
        self.assertEqual(sum_feb_2019, 20)

        sum_dec_2018 = get_system_sum_for_month(self.mpk, self.fraction, 12, 2018)
        self.assertEqual(sum_dec_2018, 100)
