#pickups/tasks.py

from celery import shared_task
import logging
from pickups.excel_generator import generate_pickup_excel
from pickups.models import Pickup
from django.core.mail import EmailMessage
from decouple import config

logger = logging.getLogger(__name__)

def wyslij_email_sync(pickup_id: int) -> str:
    """Wysyła email synchronicznie, bez Celery."""
    pickup = (
        Pickup.objects
        .select_related('location', 'mpk_number', 'reporter')
        .prefetch_related('waste_bins__waste_fraction__fraction_type__schedules')
        .get(id=pickup_id)
    )

    excel_bytes = generate_pickup_excel(pickup)
    filename = (
        f"Zgloszenie_{pickup.mpk_number.mpk_number}"
        f"_{pickup.reported_at.strftime('%Y-%m-%d')}.xlsx"
    )

    email = EmailMessage(
        subject=f"Zgłoszenie odbioru {pickup.pickup_number}",
        body=(
            f"Zgłoszenie odbioru odpadów nr {pickup.pickup_number}\n"
            f"Lokalizacja: {pickup.location}\n"
            f"Data: {pickup.reported_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Zgłaszający: {pickup.reporter.get_full_name()}"
        ),
        from_email=config("DEFAULT_FROM_EMAIL"),
        to=[config("ZGLOSZENIA_EMAIL")],
    )
    email.attach(
        filename,
        excel_bytes,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    email.send()

    pickup.status = 'WYSŁANE'
    pickup.save(update_fields=['status'])
    logger.info(f"Wysłano zgłoszenie {pickup.pickup_number}")
    return f"OK: {pickup.pickup_number}"

@shared_task(bind=True, max_retries=3)
def wyslij_zgloszenie_email(self, pickup_id: int) -> str:
    try:
        return wyslij_email_sync(pickup_id)
    except Exception as exc:
        logger.error(f"Błąd wysyłki zgłoszenia ID={pickup_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
# @shared_task(bind=True, max_retries=3)
# def wyslij_zgloszenie_email(self, pickup_id: int) -> str:
#     try:

#         pickup = (
#             Pickup.objects
#             .select_related('location', 'mpk_number', 'reporter')
#             .prefetch_related('waste_bins__waste_fraction__fraction_type')
#             .get(id=pickup_id)
#         )

#         excel_bytes = generate_pickup_excel(pickup)
#         filename = (
#             f"Zgloszenie_{pickup.mpk_number.mpk_number}"
#             f"_{pickup.reported_at.strftime('%Y-%m-%d')}.xlsx"
#         )

#         email = EmailMessage(
#             subject=f"Zgłoszenie odbioru {pickup.pickup_number}",
#             body=(
#                 f"Zgłoszenie odbioru odpadów nr {pickup.pickup_number}\n"
#                 f"Lokalizacja: {pickup.location}\n"
#                 f"Data: {pickup.reported_at.strftime('%Y-%m-%d %H:%M')}\n"
#                 f"Zgłaszający: {pickup.reporter.get_full_name()}"
#             ),
#             from_email=config("DEFAULT_FROM_EMAIL"),
#             to=['adrian.sidorek@orlen.pl'], #config("ZGLOSZENIA_EMAIL")
#         )
#         email.attach(
#             filename,
#             excel_bytes,
#             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         )
#         email.send()
        
#         pickup.status = 'WYSŁANE'
#         pickup.save(update_fields=['status'])

#         logger.info(f"Wysłano zgłoszenie {pickup.pickup_number}")
#         return f"OK: {pickup.pickup_number}"

#     except Exception as exc:
#         logger.error(f"Błąd wysyłki zgłoszenia ID={pickup_id}: {exc}")
#         raise self.retry(exc=exc, countdown=60)
    
# @shared_task(bind=True, max_retries=3)
# def wyslij_zgloszenie_email_group(self, pickup_id: int) -> str:
#     try:
#         pickup = (
#             Pickup.objects
#             .select_related('location', 'mpk_number', 'reporter')
#             .prefetch_related('waste_bins__waste_fraction__fraction_type')
#             .get(id=pickup_id)
#         )

#         # Wszystkie zgłoszenia dla tego MPK — najnowsze pierwsze
#         wszystkie_zgloszenia = (
#             Pickup.objects
#             .filter(mpk_number=pickup.mpk_number)
#             .select_related('location', 'mpk_number', 'reporter')
#             .prefetch_related('waste_bins__waste_fraction__fraction_type')
#             .order_by('-reported_at')  # newest first
#         )

#         excel_bytes = generate_mpk_history_excel(
#             new_pickup=pickup,
#             all_pickups=wszystkie_zgloszenia
#         )

#         mpk_num = pickup.mpk_number.mpk_number
#         filename = (
#             f"Historia_MPK{mpk_num}"
#             f"_{pickup.reported_at.strftime('%Y-%m-%d')}.xlsx"
#         )

#         email = EmailMessage(
#             subject=f"Zgłoszenie odbioru {pickup.pickup_number} "
#                     f"[MPK {mpk_num}]",
#             body=(
#                 f"Nowe zgłoszenie odbioru odpadów: {pickup.pickup_number}\n"
#                 f"Lokalizacja: {pickup.location}\n"
#                 f"Data: {pickup.reported_at.strftime('%Y-%m-%d %H:%M')}\n"
#                 f"Zgłaszający: {pickup.reporter.get_full_name()}\n\n"
#                 f"W załączniku historia wszystkich zgłoszeń "
#                 f"dla MPK {mpk_num} "
#                 f"({wszystkie_zgloszenia.count()} szt.)."
#             ),
#             from_email=config("DEFAULT_FROM_EMAIL"),
#             to=[config("ZGLOSZENIA_EMAIL")],
#         )
#         email.attach(
#             filename,
#             excel_bytes,
#             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         )
#         email.send()

#         pickup.status = 'WYSŁANE'
#         pickup.save(update_fields=['status', 'updated_at'])

#         logger.info(
#             f"Wysłano zgłoszenie {pickup.pickup_number} "
#             f"z historią {wszystkie_zgloszenia.count()} zgłoszeń"
#         )
#         return f"OK: {pickup.pickup_number}"

#     except Exception as exc:
#         logger.error(f"Błąd wysyłki zgłoszenia ID={pickup_id}: {exc}")
#         raise self.retry(exc=exc, countdown=60)