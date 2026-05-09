from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import pandas as pd

from reports.services import import_collection_data
from locations.models import MPKNumber
from waste.models import WasteFraction, WasteFractionType

User = get_user_model()

class ImportCollectionDataTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.mpk = MPKNumber.objects.create(mpk_number=6013)
        self.fraction_type = WasteFractionType.objects.create(code=200301, name="Zmieszane")
        self.fraction = WasteFraction.objects.create(fraction_type=self.fraction_type, capacity=120)

    @patch('reports.services.pd.read_csv')
    def test_import_missing_mpk(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            'Numer MPK': 9999,  # This MPK does not exist
            'Frakcja': 'Zmieszane',
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': None
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 0)
        self.assertEqual(results['skipped'], 0)
        self.assertEqual(results['auto_confirmed'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Błąd w wierszu 0", results['errors'][0])
        self.assertIn("MPKNumber matching query does not exist", results['errors'][0])

    @patch('reports.services.pd.read_csv')
    def test_import_missing_fraction(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            'Numer MPK': 6013,
            'Frakcja': 'NieistniejącaFrakcja', # This fraction does not exist
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': None
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 0)
        self.assertEqual(results['skipped'], 0)
        self.assertEqual(results['auto_confirmed'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Błąd w wierszu 0", results['errors'][0])
        self.assertIn("WasteFraction matching query does not exist", results['errors'][0])

    @patch('reports.services.pd.read_csv')
    def test_import_invalid_integer_data(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            'Numer MPK': 6013,
            'Frakcja': 'Zmieszane',
            'Pojemność': 'nie-liczba', # Invalid integer
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': None
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 0)
        self.assertEqual(results['skipped'], 0)
        self.assertEqual(results['auto_confirmed'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Błąd w wierszu 0", results['errors'][0])
        self.assertIn("invalid literal for int() with base 10", results['errors'][0])

    @patch('reports.services.pd.read_csv')
    def test_import_missing_column(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            # Missing 'Numer MPK'
            'Frakcja': 'Zmieszane',
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': None
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 0)
        self.assertEqual(results['skipped'], 0)
        self.assertEqual(results['auto_confirmed'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Błąd w wierszu 0", results['errors'][0])
        self.assertIn("Numer MPK", results['errors'][0])


    @patch('reports.services.pd.read_csv')
    def test_import_auto_confirmed(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            'Numer MPK': 6013,
            'Frakcja': 'Zmieszane',
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': '2023-05-15'
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        with patch('reports.services.get_system_sum_for_month') as mock_get_sum:
            mock_get_sum.return_value = 1
            with patch('reports.services.precalculate_system_sums') as mock_precalc:
                from collections import defaultdict
                mock_precalc.return_value = ({6013: self.mpk}, {('Zmieszane', 120): self.fraction}, defaultdict(int))
                results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 1)
        self.assertEqual(results['skipped'], 0)
        self.assertEqual(results['auto_confirmed'], 1)
        self.assertEqual(len(results['errors']), 0)

    @patch('reports.services.pd.read_csv')
    def test_import_skipped_existing(self, mock_read_csv):
        mock_df = pd.DataFrame([{
            'Numer MPK': 6013,
            'Frakcja': 'Zmieszane',
            'Pojemność': 120,
            'Ilość': 1,
            'Miesiąc': 5,
            'Rok': 2023,
            'Data Odbioru': '2023-05-15'
        }])
        mock_read_csv.return_value = mock_df

        file_mock = MagicMock()
        file_mock.name = 'test.csv'

        from reports.models import SummaryCollectionSchedule
        SummaryCollectionSchedule.objects.create(
            mpk_number=self.mpk,
            year=2023,
            month=5,
            waste_fraction=self.fraction,
            quantity=1,
            imported_by=self.user,
            date_summary=pd.to_datetime('2023-05-15').date()
        )

        results = import_collection_data(file_mock, self.user)

        self.assertEqual(results['imported'], 0)
        self.assertEqual(results['skipped'], 1)
        self.assertEqual(results['auto_confirmed'], 0)
        self.assertEqual(len(results['errors']), 0)
