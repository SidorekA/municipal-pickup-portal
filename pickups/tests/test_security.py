import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Permission
from locations.models import Location, MPKNumber

User = get_user_model()

@pytest.mark.django_db
def test_api_get_pickup_dates_security():
    client = Client(enforce_csrf_checks=False)
    user = User.objects.create_user(username='test', password='password')
    mpk = MPKNumber.objects.create(mpk_number=123, active=True)
    loc = Location.objects.create(localization='Loc 1', obj_name='Obj 1', mpk_number=mpk)

    url = reverse('pickups:api_pickup_dates', args=[loc.id])
    print(f"URL: {url}")

    # 2. Authenticated but no permission
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403, f"Authenticated no permission expected 403 but got {response.status_code}"
