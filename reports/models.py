# reports/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class CollectionReport(TimeStampedModel):
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="collection_reports",
    )
    pickup_date = models.DateField()
    collector_company = models.CharField(max_length=255)
    reference_document = models.CharField(max_length=128)
    report_file = models.FileField(upload_to="collection_reports/%Y/%m/", null=True, blank=True)
    request = models.OneToOneField(
        "requests.Request",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collection_report",
    )
    collected_fractions = models.JSONField()
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entered_collection_reports",
    )

    def __str__(self) -> str:
        return f"{self.location} / {self.pickup_date}"


class MonthlyConfirmation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "OCZEKUJE"
        CONFIRMED = "CONFIRMED", "POTWIERDZONE"
        APPROVED = "APPROVED", "ZATWIERDZONE"

    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="monthly_confirmations",
    )
    month = models.DateField()  # pierwszy dzień miesiąca
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    confirmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_months",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_months",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["location", "month"], name="uniq_location_month")
        ]

    def __str__(self) -> str:
        return f"{self.location} / {self.month}"