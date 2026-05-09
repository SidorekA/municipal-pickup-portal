# core/management/commands/test_excel_group.py
from django.core.management.base import BaseCommand
from pickups.models import Pickup
from pickups.excel_generator import generate_mpk_history_excel
import os


class Command(BaseCommand):
    help = 'Generuje testowy plik Excel z historią wszystkich zgłoszeń dla MPK'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pickup-id',
            type=int,
            help='ID zgłoszenia (domyślnie: pierwsze z bazy)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='test_output_group.xlsx',
            help='Ścieżka do pliku wyjściowego',
        )

    def handle(self, *args, **options):
        pickup_id = options.get('pickup_id')

        qs = (
            Pickup.objects
            .select_related('location', 'mpk_number', 'reporter')
            .prefetch_related('waste_bins__waste_fraction__fraction_type')
        )

        if pickup_id:
            pickup = qs.filter(pk=pickup_id).first()
            if not pickup:
                self.stderr.write(
                    self.style.ERROR(f'Nie znaleziono zgłoszenia ID={pickup_id}')
                )
                return
        else:
            pickup = qs.first()
            if not pickup:
                self.stderr.write(
                    self.style.ERROR('Brak zgłoszeń w bazie danych')
                )
                return

        # Wszystkie zgłoszenia dla tego MPK — najnowsze pierwsze
        wszystkie_zgloszenia = (
            Pickup.objects
            .filter(mpk_number=pickup.mpk_number)
            .select_related('location', 'mpk_number', 'reporter')
            .prefetch_related('waste_bins__waste_fraction__fraction_type')
            .order_by('-reported_at')
        )

        self.stdout.write(f'Zgłoszenie (nowe): {pickup.pickup_number}')
        self.stdout.write(f'MPK: {pickup.mpk_number}')
        self.stdout.write(f'Lokalizacja: {pickup.location}')
        self.stdout.write(f'Pojemniki w zgłoszeniu: {pickup.waste_bins.count()}')
        self.stdout.write(
            f'Wszystkich zgłoszeń dla MPK {pickup.mpk_number}: '
            f'{wszystkie_zgloszenia.count()}'
        )

        try:
            excel_bytes = generate_mpk_history_excel(
                new_pickup=pickup,
                all_pickups=wszystkie_zgloszenia
            )

            output_path = options['output']
            with open(output_path, 'wb') as f:
                f.write(excel_bytes)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Zapisano: {os.path.abspath(output_path)} '
                    f'({len(excel_bytes)} bajtów)'
                )
            )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Błąd generowania: {e}')
            )
            raise