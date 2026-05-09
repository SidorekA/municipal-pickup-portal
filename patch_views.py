import re

with open('core/views.py', 'r') as f:
    content = f.read()

imports = """
from django.apps import apps
from django.http import HttpResponse
import pandas as pd
import io
from .models import DataTransferLog
from django.db import transaction
"""

content = content.replace("from django.shortcuts import render", imports + "\nfrom django.shortcuts import render")

admin_tasks_view_replacement = """
@staff_member_required
def admin_tasks_view(request):
    \"\"\"Widok panelu zadań administracyjnych.\"\"\"
    # Pobranie wszystkich modeli z zainstalowanych aplikacji, z wykluczeniem systemowych
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']
    models_list = []
    for app_config in apps.get_app_configs():
        if app_config.name not in excluded_apps:
            for model in app_config.get_models():
                model_name = f"{app_config.label}.{model.__name__}"
                models_list.append((model_name, model._meta.verbose_name.title()))

    models_list.sort(key=lambda x: x[1])

    # Pobranie rejestru transferów
    transfer_logs = DataTransferLog.objects.all().order_by('-created_at')[:20]

    context = {
        'models_list': models_list,
        'transfer_logs': transfer_logs,
    }
    return render(request, 'core/admin_tasks.html', context)

@staff_member_required
def export_table_data_view(request):
    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        export_format = request.POST.get('export_format')

        if not model_name or not export_format:
            messages.error(request, "Wybierz tabelę i format eksportu.")
            return redirect('core:admin_tasks')

        try:
            app_label, model_class_name = model_name.split('.')
            model = apps.get_model(app_label, model_class_name)
        except LookupError:
            messages.error(request, "Nieprawidłowa tabela.")
            return redirect('core:admin_tasks')

        queryset = model.objects.all()
        data = list(queryset.values())
        df = pd.DataFrame(data)

        # Remove timezone info for excel
        for col in df.select_dtypes(['datetimetz']).columns:
            df[col] = df[col].dt.tz_localize(None)

        file_name = f"{app_label}_{model_class_name}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

        response = HttpResponse()

        try:
            if export_format == 'csv':
                response['Content-Type'] = 'text/csv'
                response['Content-Disposition'] = f'attachment; filename={file_name}.csv'
                df.to_csv(path_or_buf=response, index=False, encoding='utf-8')
            elif export_format == 'xlsx':
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)

            # Zapis do logu
            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=len(df),
                status='SUCCESS'
            )
            return response

        except Exception as e:
            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=0,
                status='ERROR',
                details=str(e)
            )
            messages.error(request, f"Błąd eksportu: {str(e)}")
            return redirect('core:admin_tasks')

    return redirect('core:admin_tasks')

@staff_member_required
def import_table_data_view(request):
    if request.method == 'POST' and request.FILES.get('data_file'):
        model_name = request.POST.get('model_name')
        data_file = request.FILES['data_file']

        if not model_name:
            messages.error(request, "Wybierz tabelę do importu.")
            return redirect('core:admin_tasks')

        if not data_file.name.endswith(('.xlsx', '.csv')):
            messages.error(request, "Nieprawidłowy format pliku. Proszę wgrać plik .xlsx lub .csv")
            return redirect('core:admin_tasks')

        try:
            app_label, model_class_name = model_name.split('.')
            model = apps.get_model(app_label, model_class_name)
        except LookupError:
            messages.error(request, "Nieprawidłowa tabela.")
            return redirect('core:admin_tasks')

        try:
            if data_file.name.endswith('.csv'):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)

            # Remove NaNs
            df = df.where(pd.notnull(df), None)

            records_created = 0
            records_updated = 0
            errors = []

            # Pobieranie wszystkich relacji FK, aby poprawić mapowanie
            fk_fields = {f.name: f for f in model._meta.fields if f.is_relation and f.many_to_one}

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        row_dict = row.to_dict()
                        clean_dict = {}

                        for key, value in row_dict.items():
                            if pd.isna(value):
                                clean_dict[key] = None
                            else:
                                clean_dict[key] = value

                            # Konwersja _id fields if present
                            if key in fk_fields and key + '_id' not in clean_dict:
                                # This is a bit naive, might need more robust handling if people export/import IDs
                                pass

                        if 'id' in clean_dict and clean_dict['id'] is not None:
                            obj_id = clean_dict.pop('id')
                            obj, created = model.objects.update_or_create(id=obj_id, defaults=clean_dict)
                            if created:
                                records_created += 1
                            else:
                                records_updated += 1
                        else:
                            clean_dict.pop('id', None)
                            obj, created = model.objects.get_or_create(**clean_dict)
                            if created:
                                records_created += 1

                    except Exception as e:
                        errors.append(f"Wiersz {index+2}: {str(e)}")

            status = 'SUCCESS'
            details = f"Utworzono: {records_created}, Zaktualizowano/Pominięto: {records_updated}"
            if errors:
                status = 'PARTIAL' if records_created > 0 or records_updated > 0 else 'ERROR'
                details += "\nBłędy:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    details += f"\n...oraz {len(errors) - 10} innych."

            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=len(df),
                status=status,
                details=details
            )

            if status in ['SUCCESS', 'PARTIAL']:
                msg = f"Import zakończony. Utworzono: {records_created}, Zaktualizowano: {records_updated}."
                if errors:
                    messages.warning(request, f"{msg} Wystąpiły błędy (sprawdź rejestr).")
                else:
                    messages.success(request, msg)
            else:
                messages.error(request, "Import zakończony niepowodzeniem (sprawdź rejestr).")

        except Exception as e:
            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=0,
                status='ERROR',
                details=str(e)
            )
            messages.error(request, f"Błąd podczas parsowania pliku: {str(e)}")

    return redirect('core:admin_tasks')
"""

content = re.sub(
    r'@staff_member_required\ndef admin_tasks_view\(request\):\n\s+"""Widok panelu zadań administracyjnych."""\n\s+return render\(request, \'core/admin_tasks\.html\'\)',
    admin_tasks_view_replacement.strip(),
    content
)

with open('core/views.py', 'w') as f:
    f.write(content)
