from celery import shared_task
import logging
from django.core.mail import EmailMessage
from django.conf import settings


logger = logging.getLogger(__name__)


@shared_task
def ping() -> str:
    return "pong"

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def wyslij_zgloszenie_email(self, pickup_id: int) -> str:
    try:
        from .models import Pickup
        from .excel_generator import generate_pickup_excel

        pickup = (
            Pickup.objects
            .select_related('location', 'mpk_number', 'reporter')
            .prefetch_related('waste_bins__waste_fraction__fraction_type')
            .get(id=pickup_id)
        )

        # Generuj plik
        excel_bytes = generate_pickup_excel(pickup)
        filename = (
            f"Zgloszenie_{pickup.mpk_number.mpk_number}"
            f"_{pickup.reported_at.strftime('%Y-%m-%d')}.xlsx"
        )

        # Wyślij email z załącznikiem
        email = EmailMessage(
            subject=f"Zgłoszenie odbioru {pickup.pickup_number}",
            body=(
                f"Zgłoszenie odbioru odpadów nr {pickup.pickup_number}\n"
                f"Lokalizacja: {pickup.location}\n"
                f"Data: {pickup.reported_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"Zgłaszający: {pickup.reporter.get_full_name()}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ZGLOSZENIA_EMAIL],
        )
        email.attach(
            filename,
            excel_bytes,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        email.send()

        # Zmień status na WYSŁANE
        pickup.status = 'WYSŁANE'
        pickup.save(update_fields=['status'])

        logger.info(f"Wysłano zgłoszenie {pickup.pickup_number}")
        return f"OK: {pickup.pickup_number}"

    except Exception as exc:
        logger.error(f"Błąd wysyłki zgłoszenia ID={pickup_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)  # ponów za 60 sek