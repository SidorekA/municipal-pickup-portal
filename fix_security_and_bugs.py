with open('core/views.py', 'r') as f:
    content = f.read()

# 1. Extract excluded_apps to a constant or check in both views
excluded_apps_def = "EXCLUDED_APPS = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']\n"

# Add it after imports
import_end = content.find('\n@staff_member_required')
content = content[:import_end] + "\n\n" + excluded_apps_def + content[import_end:]

# 2. Update admin_tasks_view to use the constant
content = content.replace("excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']\n    models_list = []", "models_list = []")
content = content.replace("if app_config.name not in excluded_apps:", "if app_config.name not in EXCLUDED_APPS:")

# 3. Fix export_table_data_view
export_view_start = content.find("def export_table_data_view(request):")
export_view_end = content.find("def import_table_data_view(request):")
export_view = content[export_view_start:export_view_end]

export_view = export_view.replace(
"""        try:
            app_label, model_class_name = model_name.split('.')
            model = apps.get_model(app_label, model_class_name)""",
"""        try:
            app_label, model_class_name = model_name.split('.')
            if app_label in EXCLUDED_APPS:
                messages.error(request, "Eksport z tej tabeli jest zabroniony.")
                return redirect('core:admin_tasks')
            model = apps.get_model(app_label, model_class_name)"""
)

export_view = export_view.replace(
"""            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=len(df),
                status='SUCCESS'
            )""",
"""            # Zapis do logu
            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=len(df),
                status='SUCCESS',
                created_by=request.user
            )"""
)

export_view = export_view.replace(
"""            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=0,
                status='ERROR',
                details=str(e)
            )""",
"""            DataTransferLog.objects.create(
                action='EXPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=f"{file_name}.{export_format}",
                records_count=0,
                status='ERROR',
                details=str(e),
                created_by=request.user
            )"""
)

# 4. Fix import_table_data_view
import_view_start = content.find("def import_table_data_view(request):")
import_view_end = len(content)
import_view = content[import_view_start:import_view_end]

import_view = import_view.replace(
"""        try:
            app_label, model_class_name = model_name.split('.')
            model = apps.get_model(app_label, model_class_name)""",
"""        try:
            app_label, model_class_name = model_name.split('.')
            if app_label in EXCLUDED_APPS:
                messages.error(request, "Import do tej tabeli jest zabroniony.")
                return redirect('core:admin_tasks')
            model = apps.get_model(app_label, model_class_name)"""
)

# Fix transaction issue - wrap inner logic in transaction.atomic()
inner_tx = """                for index, row in df.iterrows():
                    try:
                        with transaction.atomic():
                            row_dict = row.to_dict()
                            clean_dict = {}

                            for key, value in row_dict.items():
                                if pd.isna(value):
                                    clean_dict[key] = None
                                else:
                                    clean_dict[key] = value

                                # Konwersja _id fields if present
                                if key in fk_fields and key + '_id' not in clean_dict:
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
                        errors.append(f"Wiersz {index+2}: {str(e)}")"""

import_view = import_view.replace(
"""                for index, row in df.iterrows():
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
                        errors.append(f"Wiersz {index+2}: {str(e)}")""", inner_tx)

import_view = import_view.replace(
"""            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=len(df),
                status=status,
                details=details
            )""",
"""            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=len(df),
                status=status,
                details=details,
                created_by=request.user
            )"""
)

import_view = import_view.replace(
"""            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=0,
                status='ERROR',
                details=str(e)
            )""",
"""            DataTransferLog.objects.create(
                action='IMPORT',
                table_name=f"{model._meta.verbose_name} ({model_name})",
                file_name=data_file.name,
                records_count=0,
                status='ERROR',
                details=str(e),
                created_by=request.user
            )"""
)

# Reassemble
content = content[:export_view_start] + export_view + import_view

with open('core/views.py', 'w') as f:
    f.write(content)
