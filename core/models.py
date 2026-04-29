# core/models.py
from __future__ import annotations

from django.db import models


class CoreModel(models.Model):
    """Domyślna baza dla wszystkich modeli, zawierająca pola wspólne."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data modyfikacji')
    note = models.TextField(blank=True, default='', verbose_name='Uwagi')

    class Meta:
        abstract = True