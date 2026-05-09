import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import DataTransferLog
from waste.models import WasteFractionType

User = get_user_model()

@pytest.mark.django_db
def test_export_table_data(client):
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    client.force_login(user)

    WasteFractionType.objects.create(name='Plastik', code=101, active=True)

    url = reverse('core:export_table_data')
    data = {
        'model_name': 'waste.WasteFractionType',
        'export_format': 'csv'
    }
    response = client.post(url, data)

    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv'
    assert 'Plastik' in response.content.decode('utf-8')
    assert DataTransferLog.objects.filter(action='EXPORT').count() == 1

@pytest.mark.django_db
def test_import_table_data(client, tmp_path):
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    client.force_login(user)

    csv_content = "name,code,active\nSzkło,102,True\n"
    csv_file = tmp_path / "import.csv"
    csv_file.write_text(csv_content, encoding='utf-8')

    url = reverse('core:import_table_data')

    with open(csv_file, 'rb') as f:
        data = {
            'model_name': 'waste.WasteFractionType',
            'data_file': f
        }
        response = client.post(url, data)

    assert response.status_code == 302
    assert WasteFractionType.objects.filter(name='Szkło').exists()
    assert DataTransferLog.objects.filter(action='IMPORT').count() == 1


@pytest.mark.django_db
def test_export_security(client):
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    client.force_login(user)

    url = reverse('core:export_table_data')
    data = {
        'model_name': 'auth.User',
        'export_format': 'csv'
    }
    response = client.post(url, data)
    assert response.status_code == 302
    # Should redirect with error msg instead of serving file
