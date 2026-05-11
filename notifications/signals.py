from django.db.models.signals import post_save
from django.dispatch import receiver
from reports.models import MonthlyConfirmation
from users.models import Permission
from .models import Notification

@receiver(post_save, sender=MonthlyConfirmation)
def notify_on_monthly_confirmation(sender, instance, created, **kwargs):
    """
    Tworzy powiadomienie, gdy administrator doda/zatwierdzi potwierdzenie miesięczne.
    """
    # Check if the user who created/updated it is a staff/admin.
    # Note: `created_by` or `updated_by` comes from CoreModel.
    # For approval, we also check `approved_by`.

    acting_user = instance.updated_by or instance.created_by
    if acting_user and acting_user.is_staff:
        # Find all users linked to this MPKNumber with an active permission
        permissions = Permission.objects.filter(
            mpk_number=instance.mpk_number,
            active=True
        )

        # Prepare the message depending on the status and if it was just created
        month_str = instance.month.strftime("%Y-%m")
        if created:
            message = f"Administrator dodał nowe potwierdzenie dla MPK {instance.mpk_number} za miesiąc {month_str}. Status: {instance.get_status_display()}"
        else:
            # We notify if the status was changed to something meaningful, like ZATWIERDZONE
            # A more robust check might track previous status, but post_save doesn't have it easily.
            # Assuming any staff update is worth notifying:
            message = f"Administrator zaktualizował potwierdzenie dla MPK {instance.mpk_number} za miesiąc {month_str}. Nowy status: {instance.get_status_display()}"

        # Create notifications
        notifications_to_create = []
        for perm in permissions:
            # Avoid notifying the admin who did it, optionally
            if perm.user != acting_user:
                notifications_to_create.append(
                    Notification(user=perm.user, message=message)
                )

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
