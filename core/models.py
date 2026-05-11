# core/models.py
from __future__ import annotations
from django.conf import settings
from crum import get_current_user
from django.db import models

class CoreModel(models.Model):
    """Domyślna baza dla wszystkich modeli, zawierająca pola wspólne."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data modyfikacji')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name='Utworzył'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name='Zmodyfikował'
    )
    note = models.TextField(blank=True, default='', verbose_name='Uwagi')
    
    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and not user.is_anonymous:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
class DataTransferLog(CoreModel):
    ACTION_CHOICES = [
        ('EXPORT', 'Eksport'),
        ('IMPORT', 'Import'),
    ]
    STATUS_CHOICES = [
        ('SUCCESS', 'Sukces'),
        ('ERROR', 'Błąd'),
        ('PARTIAL', 'Częściowy sukces'),
    ]

    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='Akcja')
    table_name = models.CharField(max_length=100, verbose_name='Tabela')
    file_name = models.CharField(max_length=255, verbose_name='Nazwa pliku')
    records_count = models.IntegerField(default=0, verbose_name='Liczba rekordów')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SUCCESS', verbose_name='Status')
    details = models.TextField(blank=True, verbose_name='Szczegóły (błędy/ostrzeżenia)')

    class Meta:
        verbose_name = 'Rejestr transferu danych'
        verbose_name_plural = 'Rejestry transferu danych'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.table_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
