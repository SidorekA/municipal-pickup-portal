from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import datetime
from .models import Notification, NotificationSetting
from reports.models import SummaryCollectionSchedule, MonthlyConfirmation
from users.models import Permission

@shared_task
def check_overdue_confirmations():
    """
    Codziennie sprawdza, czy nie minął próg dni na zatwierdzenie raportów
    z poprzedniego miesiąca. Jeśli tak, generuje przypomnienia.
    """
    today = timezone.now().date()

    try:
        setting = NotificationSetting.objects.get(pk=1)
        threshold_days = setting.reminder_threshold_days
    except NotificationSetting.DoesNotExist:
        threshold_days = 5

    # Check only if today's day is greater than or equal to threshold
    if today.day < threshold_days:
        return f"Za wcześnie na przypomnienia (dzień {today.day} < próg {threshold_days})"

    # Calculate previous month
    # A safe way is to take the first day of current month and subtract 1 day
    first_day_current_month = today.replace(day=1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    target_year = last_day_prev_month.year
    target_month = last_day_prev_month.month

    # Get MPKs that have imported data for the target month
    # but lack a fully confirmed MonthlyConfirmation

    # 1. MPKs with imported data
    mpks_with_data = SummaryCollectionSchedule.objects.filter(
        year=target_year,
        month=target_month
    ).values_list('mpk_number', flat=True).distinct()

    # 2. Find which of these MPKs have missing or incomplete confirmations
    first_day_target_month = datetime.date(target_year, target_month, 1)

    completed_statuses = ['POTWIERDZONE', 'ZATWIERDZONE', 'KONFLIKT']

    # We want MPKs that are in mpks_with_data BUT NOT in (confirmations with completed_statuses)
    completed_confirmations_mpks = MonthlyConfirmation.objects.filter(
        month=first_day_target_month,
        status__in=completed_statuses
    ).values_list('mpk_number', flat=True)

    overdue_mpks = set(mpks_with_data) - set(completed_confirmations_mpks)

    if not overdue_mpks:
        return "Brak zaległych potwierdzeń."

    notifications_to_create = []

    # Generate notifications for each user linked to these MPKs
    for mpk_id in overdue_mpks:
        permissions = Permission.objects.filter(mpk_number_id=mpk_id, active=True)

        message = f"Przypomnienie: Potwierdzenie miesięczne dla MPK {mpk_id} za {target_year}-{target_month:02d} jest zaległe."

        for perm in permissions:
            # Optionally check if a similar unread notification already exists to avoid spamming daily
            already_notified = Notification.objects.filter(
                user=perm.user,
                message=message,
                is_read=False,
                created_at__date=today # Or just check if exists at all for this month
            ).exists()

            if not already_notified:
                notifications_to_create.append(
                    Notification(user=perm.user, message=message)
                )

    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)
        return f"Utworzono {len(notifications_to_create)} powiadomień przypominających."

    return "Brak nowych powiadomień do wysłania (już wysłane)."
