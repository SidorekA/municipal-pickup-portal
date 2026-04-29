# scheduling/models.py

from django.db import models

from core.models import CoreModel

class CollectionSchedule(CoreModel):
    """Harmonogram odbiorów."""
    DAY_CHOICES = [
        (1, 'Poniedziałek'), (2, 'Wtorek'), (3, 'Środa'),
        (4, 'Czwartek'), (5, 'Piątek'),
    ]
    fraction_type = models.ForeignKey(
        'locations.WasteFractionType',
        on_delete=models.PROTECT,
        related_name='schedules',
        verbose_name='Rodzaj frakcji'
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES, 
        verbose_name='Dzień tygodnia'
    )
    active = models.BooleanField(
        default=True, 
        verbose_name='Aktywny')

    class Meta:
        verbose_name = 'Harmonogram odbioru'
        verbose_name_plural = 'Harmonogram odbiorów'
        ordering = ['day_of_week']

    def __str__(self):
        return f'{self.fraction_type.name} – {self.get_day_of_week_display()}'