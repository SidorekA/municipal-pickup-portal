# scheduling/tests/test_services.py

from datetime import datetime
from zoneinfo import ZoneInfo
from django.test import TestCase
from locations.models import WasteFractionType
from scheduling.models import CollectionSchedule
from scheduling.services import get_next_pickup_date

WARSAW = ZoneInfo("Europe/Warsaw")

class NextPickupDateTests(TestCase):

    def setUp(self):
        self.zmieszane = WasteFractionType.objects.create(code=200301, name="Zmieszane")
        # PN=1, ŚR=3, PT=5
        for day in [1, 3, 5]:
            CollectionSchedule.objects.create(
                fraction_type=self.zmieszane,
                day_of_week=day,
            )

    def test_poniedzialek_przed_12_daje_wtorek(self):
        submitted = datetime(2025, 1, 6, 11, 0, tzinfo=WARSAW)
        result = get_next_pickup_date(self.zmieszane, submitted)
        self.assertEqual(result.isoweekday(), 3)

    def test_poniedzialek_po_12_omija_srode(self):
        submitted = datetime(2025, 1, 7, 12, 30, tzinfo=WARSAW)
        result = get_next_pickup_date(self.zmieszane, submitted)
        self.assertEqual(result.isoweekday(), 5)

    def test_brak_harmonogramu_zwraca_none(self):
        pusta = WasteFractionType.objects.create(code=999999, name="Zmieszane2")
        result = get_next_pickup_date(pusta)
        self.assertIsNone(result)