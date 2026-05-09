from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import CoreModel
class UserProfile(CoreModel):
    """Dodatkowe informacje o użytkowniku."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=32, 
                             blank=True, 
                             verbose_name='Telefon'
                             )
    department_short = models.CharField(max_length=10, 
                                        blank=False, 
                                        verbose_name='Skrót jednostki'
                                        )
    department_name = models.CharField(max_length=128, 
                                       blank=False, 
                                       verbose_name='Nazwa jednostki'
                                       )
    
    class Meta:
        verbose_name = 'Profil użytkownika'
        verbose_name_plural = 'Profile użytkowników'

    def __str__(self) -> str:
        return f"{self.user.username}"

class Permission(CoreModel):
    """Uprawnienia użytkownika do zarządzania zgłoszeniami dla konkretnego MPK."""
    class Role(models.TextChoices):
        REPORTER = "REPORTER", "ZGŁASZAJĄCY"
        VERIFIER = "VERIFIER", "WERYFIKATOR"
        ADMINISTRATOR = "ADMINISTRATOR", "ADMINISTRATOR"
        VIEWER = "VIEWER", "ODWIEDZAJĄCY"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mpk_permissions",
        verbose_name='Uprawnienia',
    )
    mpk_number = models.ForeignKey(
        "locations.MPKNumber",
        on_delete=models.CASCADE,
        related_name="mpk_permissions",
        verbose_name='Lokalizacja',
    )
    role = models.CharField(max_length=32, 
                            choices=Role.choices, 
                            verbose_name='Rola'
                            )
    active = models.BooleanField(default=True, 
                                 verbose_name='Aktywny'
                                 )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_permissions",
    )

    class Meta:
        verbose_name = 'Uprawnienie'
        verbose_name_plural = 'Uprawnienia'
        ordering = ['mpk_number__mpk_number']
        
        constraints = [
            models.UniqueConstraint(
                fields=["user", "mpk_number", "role"],
                name="uniq_user_mpk_number_role",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["REPORTER", "VERIFIER", "ADMINISTRATOR", "VIEWER"]),
                name="chk_valid_role"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.mpk_number} [{self.role}]"
    
class Coordinator(CoreModel):
    """Koordynator lokalizacji."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coordinations",
        verbose_name='Koordynator',
    )
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.CASCADE,
        related_name="coordinators",
        verbose_name='Lokalizacja',
    )
    active = models.BooleanField(default=True, verbose_name='Aktywny')

    class Meta:
        verbose_name = 'Koordynator'
        verbose_name_plural = 'Koordynatorzy'
        ordering = ['location__obj_name', 'user__username']
        
        constraints = [
            models.UniqueConstraint(
                fields=["user", "location"],
                name="uniq_user_location",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.location}"