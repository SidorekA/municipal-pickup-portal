# requests/models.py
from __future__ import annotations
from django.conf import settings
from django.db import models
from core.models import CoreModel
from django.utils import timezone

class Pickup(CoreModel):
    """Zgłoszenie odbioru odpadów."""
    STATUS_CHOICES = [
        ('NOWE', 'Nowe'),
        ('WYSŁANE', 'Wysłane'),
        ('POTWIERDZONE', 'Potwierdzone'),
        ('ZREALIZOWANE', 'Zrealizowane'),
        ('ODRZUCONE', 'Odrzucone'),
    ]

    pickup_number = models.CharField(
        max_length=15, 
        verbose_name='Numer zgłoszenia'
        )
    location = models.ForeignKey(
        'locations.Location', 
        on_delete=models.PROTECT,
        related_name='pickups', 
        verbose_name='Lokalizacja'
    )
    mpk_number = models.ForeignKey(
        'locations.MPKNumber', 
        on_delete=models.PROTECT,
        related_name='pickups', 
        verbose_name='Numer MPK'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='reported_pickups', 
        verbose_name='Zgłaszający'
    )
    reported_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Data zgłoszenia'
        )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='NOWE', 
        verbose_name='Status'
    )


    class Meta:
        verbose_name = 'Zgłoszenie'
        verbose_name_plural = 'Zgłoszenia'
        ordering = ['-reported_at']

    def __str__(self):
        return f'{self.pickup_number} ({self.get_status_display()})'
    
    def save(self, *args, **kwargs):
        """Auto-generowanie numeru zgłoszenia jeśli brak."""
        if not self.pickup_number:
            last = Pickup.objects.filter(
                pickup_number__startswith=f'ZGL-{self.mpk_number}-'
            ).order_by('-pickup_number').first()
            if last:
                try:
                    seq = int(last.pickup_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.pickup_number = f'ZGL-{self.mpk_number}-{seq:05d}'
        super().save(*args, **kwargs)

class PickupWasteBin(models.Model):
    """Pojemniki w zgłoszeniu."""
    pickup = models.ForeignKey(
        Pickup, 
        on_delete=models.CASCADE,
        related_name='waste_bins', 
        verbose_name='Zgłoszenie'
    )
    waste_fraction = models.ForeignKey(
        'locations.WasteFraction', 
        on_delete=models.PROTECT,
        related_name='pickup_bins', 
        verbose_name='Frakcja'
    )
    quantity = models.PositiveIntegerField(
        default=1, 
        verbose_name='Ilość pojemników'
        )

    class Meta:
        verbose_name = 'Frakcja zgłoszenia'
        verbose_name_plural = 'Frakcje zgłoszenia'
        unique_together = [('pickup', 'waste_fraction')]

    def __str__(self):
        return f'{self.pickup.pickup_number} – {self.waste_fraction.fraction_type.name} x{self.quantity}'