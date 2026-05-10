import os
import django
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from locations.models import Location, MPKNumber, LocationContact, LocationWasteBin
from waste.models import WasteFraction, WasteFractionType
from pickups.models import Pickup
from reports.models import MonthlyConfirmation
from users.models import Permission

User = get_user_model()

def create_data():
    if not User.objects.filter(username="testuser").exists():
        user = User.objects.create_superuser("testuser", "test@example.com", "password", last_login=timezone.now())
    else:
        user = User.objects.get(username="testuser")
        user.set_password("password")
        user.save()

    mpk, _ = MPKNumber.objects.get_or_create(mpk_number="12345", defaults={"active": True})
    Permission.objects.get_or_create(user=user, mpk_number=mpk, role="REPORTER", defaults={"active": True})

    loc, _ = Location.objects.get_or_create(
        mpk_number=mpk, localization="Test Localization", obj_name="Test Obj", defaults={"active": True}
    )

    LocationContact.objects.get_or_create(
        location=loc, phone_number="123456789", contact_name="Test Contact", defaults={"active": True}
    )

    frac_type, _ = WasteFractionType.objects.get_or_create(name="Zmieszane", defaults={"active": True, "code": 1})
    waste_frac, _ = WasteFraction.objects.get_or_create(fraction_type=frac_type, capacity=120)
    LocationWasteBin.objects.get_or_create(location=loc, waste_fraction=waste_frac, defaults={"quantity": 5})

    # Reports
    today = timezone.now()
    first_day_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    mc, created = MonthlyConfirmation.objects.get_or_create(
        mpk_number=mpk,
        month=first_day_month.date(),
        defaults={"status": "OCZEKUJE"}
    )
    if created:
        mc.created_by = user
        mc.save()

    # Create monthly confirmation bins for the conflict view
    from reports.models import MonthlyConfirmationBin
    MonthlyConfirmationBin.objects.get_or_create(
        confirmation=mc,
        waste_fraction=waste_frac,
        defaults={"confirmed_quantity": 5}
    )

    # Add a pickup
    pk, created = Pickup.objects.get_or_create(
        mpk_number=mpk, location=loc, contact_phone="123456789", reporter=user,
        status="NOWE", defaults={"reported_at": timezone.now()}
    )

    from notifications.models import Notification
    Notification.objects.get_or_create(
        user=user, message="New test notification", defaults={"is_read": False}
    )

    print(f"Test data created successfully for MPK {mpk.id}, Month: {first_day_month.month}, Year: {first_day_month.year}")

if __name__ == "__main__":
    create_data()
