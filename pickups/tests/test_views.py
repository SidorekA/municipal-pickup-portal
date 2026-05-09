from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from locations.models import Location, MPKNumber
from users.models import Permission

User = get_user_model()

class ApiGetMpkLocationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Tworzenie uzytkownikow
        self.no_perm_user = User.objects.create_user(username='noperm', password='123')
        self.perm_user = User.objects.create_user(username='withperm', password='123')
        self.super_user = User.objects.create_superuser(username='super', password='123')

        # Tworzenie MPK i lokalizacji
        self.mpk1 = MPKNumber.objects.create(mpk_number=1001)
        self.mpk2 = MPKNumber.objects.create(mpk_number=1002)

        self.loc1 = Location.objects.create(mpk_number=self.mpk1, localization="Loc1", obj_name="Obj1")
        self.loc2 = Location.objects.create(mpk_number=self.mpk1, localization="Loc2", obj_name="Obj2")
        self.loc3 = Location.objects.create(mpk_number=self.mpk2, localization="Loc3", obj_name="Obj3")

        # Dodawanie uprawnien
        Permission.objects.create(user=self.perm_user, mpk_number=self.mpk1, role=Permission.Role.REPORTER, active=True)

        self.url = reverse('pickups:api_mpk_locations', args=[self.mpk1.id])

    def test_no_permission_user(self):
        self.client.force_login(self.no_perm_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['locations'], [])
        self.assertEqual(data['error'], 'Brak uprawnień do tego MPK')

    def test_permission_user(self):
        self.client.force_login(self.perm_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['locations']), 2)

        locations = data['locations']
        # Sprawdzanie czy zwrocone lokalizacje maja poprawny format nazwy
        self.assertTrue(any(loc['name'] == f"{self.loc1.localization} - {self.loc1.obj_name}" for loc in locations))
        self.assertTrue(any(loc['name'] == f"{self.loc2.localization} - {self.loc2.obj_name}" for loc in locations))

    def test_superuser(self):
        self.client.force_login(self.super_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['locations']), 2)

    def test_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['locations'], [])
        self.assertEqual(data['error'], 'Brak uprawnień do tego MPK')
