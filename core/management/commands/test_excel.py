# core/management/commands/test_excel.py
from django.core.management.base import BaseCommand
from pickups.models import Pickup
from pickups.excel_generator import generate_pickup_excel
import os


class Command(BaseCommand):
    help = 'Generuje testowy plik Excel ze zgłoszenia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pickup-id',
            type=int,
            help='ID zgłoszenia (domyślnie: pierwsze z bazy)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='test_output.xlsx',
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

        self.stdout.write(f'Zgłoszenie: {pickup.pickup_number}')
        self.stdout.write(f'MPK: {pickup.mpk_number}')
        self.stdout.write(f'Lokalizacja: {pickup.location}')
        self.stdout.write(
            f'Pojemniki: '
            f'{pickup.waste_bins.count()}'
        )

        try:
            excel_bytes = generate_pickup_excel(pickup)

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