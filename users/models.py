from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    department = models.CharField(max_length=128, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username}"


class Permission(TimeStampedModel):
    class Role(models.TextChoices):
        REPORTER = "REPORTER", "ZGŁASZAJĄCY"
        VERIFIER = "VERIFIER", "WERYFIKATOR"
        ADMINISTRATOR = "ADMINISTRATOR", "ADMINISTRATOR"
        VIEWER = "VIEWER", "ODWIEDZAJĄCY"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    active = models.BooleanField(default=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "location", "role"],
                name="uniq_user_location_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.location} [{self.role}]"