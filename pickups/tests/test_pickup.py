from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from pickups.models import Pickup, PickupWasteBin
from locations.models import Location, MPKNumber
from waste.models import WasteFraction, WasteFractionType

User = get_user_model()


class PickupTestCase(TestCase):
    """Testy dla modelu Pickup."""

    def setUp(self):
        """Dane wspólne dla wszystkich testów."""
        self.user = User.objects.create_user(
            username="Karolina",
            password="tajnehaslo",
        )
        self.mpk = MPKNumber.objects.create(mpk_number=6013)
        self.location = Location.objects.create(
            obj_name="BOŚ",
            mpk_number=self.mpk,
            )
        

    def _create_pickup(self, **kwargs):
        """Helper — tworzy Pickup z domyślnymi wartościami."""
        defaults = dict(
            location=self.location,
            mpk_number=self.mpk,
            reporter=self.user,
        )
        defaults.update(kwargs)
        return Pickup.objects.create(**defaults)

    def test_pickup_number_auto_generated(self):
        """Numer zgłoszenia generuje się automatycznie gdy nie podano."""
        pickup = self._create_pickup()
        self.assertTrue(pickup.pickup_number.startswith("ZGL-6013-"))

    def test_pickup_number_increments(self):
        """Kolejne zgłoszenia mają rosnące numery."""
        pickup1 = self._create_pickup()
        pickup2 = self._create_pickup()
        self.assertEqual(pickup1.pickup_number, "ZGL-6013-00001")
        self.assertEqual(pickup2.pickup_number, "ZGL-6013-00002")

    def test_pickup_number_separate_per_mpk(self):
        """Sekwencja numerów jest oddzielna dla każdego MPK."""
        mpk2 = MPKNumber.objects.create(mpk_number=6014)
        pickup1 = self._create_pickup()                          # MPK-6013
        pickup2 = self._create_pickup(mpk_number=mpk2)
        self.assertEqual(pickup1.pickup_number, "ZGL-6013-00001")
        self.assertEqual(pickup2.pickup_number, "ZGL-6014-00001")

    def test_default_status_is_nowe(self):
        """Nowe zgłoszenie ma status NOWE."""
        pickup = self._create_pickup()
        self.assertEqual(pickup.status, "NOWE")


class PickupWasteBinTestCase(TestCase):
    """Testy dla modelu PickupWasteBin."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="Karolina", 
            password="tajnehaslo"
            )
        self.mpk = MPKNumber.objects.create(mpk_number=6013)
        location = Location.objects.create(
            obj_name="BOŚ",
            mpk_number=self.mpk,
            )
        self.pickup = Pickup.objects.create(
            location=location,
            mpk_number=self.mpk,
            reporter=self.user,
        )

        fraction_type = WasteFractionType.objects.create(
            code=200301,
            name="Zmieszane"
        )
        self.fraction = WasteFraction.objects.create(
            fraction_type=fraction_type,
            capacity=120,                
            unit="l",                      
        )

    def test_create_waste_bin(self):
        """Można utworzyć pojemnik z domyślną ilością 1."""
        bin = PickupWasteBin.objects.create(
            pickup=self.pickup,
            waste_fraction=self.fraction,
        )
        self.assertEqual(bin.quantity, 1)

    def test_custom_quantity(self):
        """Można ustawić dowolną ilość pojemników."""
        bin = PickupWasteBin.objects.create(
            pickup=self.pickup,
            waste_fraction=self.fraction,
            quantity=5,
        )
        self.assertEqual(bin.quantity, 5)

    def test_unique_together_pickup_fraction(self):
        """Ta sama frakcja nie może pojawić się dwa razy w jednym zgłoszeniu."""
        PickupWasteBin.objects.create(
            pickup=self.pickup,
            waste_fraction=self.fraction,
        )
        with self.assertRaises(IntegrityError):
            PickupWasteBin.objects.create(
                pickup=self.pickup,
                waste_fraction=self.fraction,
            )

    def test_waste_bins_deleted_with_pickup(self):
        """Usunięcie zgłoszenia kasuje powiązane pojemniki (CASCADE)."""
        PickupWasteBin.objects.create(
            pickup=self.pickup,
            waste_fraction=self.fraction,
        )
        self.pickup.delete()
        self.assertEqual(PickupWasteBin.objects.count(), 0)


    def test_str_representation(self):
        """__str__ zawiera numer zgłoszenia, kod frakcji i ilość."""
        bin = PickupWasteBin.objects.create(
            pickup=self.pickup,
            waste_fraction=self.fraction,
            quantity=3,
        )
        self.assertIn("ZGL-6013-00001", str(bin))
        self.assertIn("Zmieszane", str(bin))
        self.assertIn("x3", str(bin))