from django.db import models
from django.conf import settings
from core.models import CoreModel

class Notification(CoreModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Użytkownik'
    )
    message = models.TextField(verbose_name='Wiadomość')
    is_read = models.BooleanField(default=False, verbose_name='Przeczytane')

    class Meta:
        verbose_name = 'Powiadomienie'
        verbose_name_plural = 'Powiadomienia'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{'Przeczytane' if self.is_read else 'Nieprzeczytane'}] {self.user} - {self.message[:50]}"

class NotificationSetting(CoreModel):
    """Singleton model for notification settings."""
    reminder_threshold_days = models.PositiveIntegerField(
        default=5,
        verbose_name='Próg dni dla przypomnień',
        help_text='Dzień miesiąca, po którym generowane są przypomnienia o braku potwierdzenia.'
    )

    class Meta:
        verbose_name = 'Ustawienia powiadomień'
        verbose_name_plural = 'Ustawienia powiadomień'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Ustawienia powiadomień (próg: {self.reminder_threshold_days} dni)"
