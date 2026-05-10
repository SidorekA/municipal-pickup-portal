from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification
from reports.models import MonthlyConfirmation
from locations.models import MPKNumber
from users.models import Permission

User = get_user_model()

class NotificationSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.staff_user = User.objects.create_user(username='adminuser', password='password', is_staff=True)
        self.mpk = MPKNumber.objects.create(mpk_number=12345)

        # Give permission to testuser
        Permission.objects.create(
            user=self.user,
            mpk_number=self.mpk,
            role='REPORTER',
            active=True
        )

    def test_monthly_confirmation_creation_triggers_notification(self):
        # Admin creates MonthlyConfirmation
        first_day = timezone.now().replace(day=1).date()

        # In testing without request, we need to mock current user or assign explicitly
        # But signals are triggered synchronously on `.create()`.
        # To avoid the signal triggering with `None` acting user, let's mock it
        from unittest.mock import patch

        with patch('core.models.get_current_user', return_value=self.staff_user):
            MonthlyConfirmation.objects.create(
                mpk_number=self.mpk,
                month=first_day,
                status='POTWIERDZONE'
            )

        # Notification should be created for testuser
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.user)
        self.assertIn('dodał nowe potwierdzenie', notification.message)
