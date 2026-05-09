from auditlog.models import LogEntry
import pandas as pd
from django.utils import timezone
import datetime
import json

def generate_auditlog_export(date_from=None, date_to=None, user_id=None, content_type_id=None):
    """
    Generates an export of audit log entries based on provided filters.
    Returns a pandas DataFrame.
    """
    queryset = LogEntry.objects.all().select_related('actor', 'content_type').order_by('-timestamp')

    if date_from:
        try:
            date_from_obj = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
            dt_from = timezone.make_aware(datetime.datetime.combine(date_from_obj, datetime.time.min))
            queryset = queryset.filter(timestamp__gte=dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
            dt_to = timezone.make_aware(datetime.datetime.combine(date_to_obj, datetime.time.max))
            queryset = queryset.filter(timestamp__lte=dt_to)
        except ValueError:
            pass

    if user_id:
        queryset = queryset.filter(actor_id=user_id)

    if content_type_id:
        queryset = queryset.filter(content_type_id=content_type_id)

    # Action choices mapping
    # 0 = create, 1 = update, 2 = delete
    action_map = {
        0: 'Utworzenie',
        1: 'Edycja',
        2: 'Usunięcie'
    }

    data = []
    for log in queryset:
        # User formatting
        user_display = "System/Anonim"
        if log.actor:
            name = log.actor.get_full_name()
            email = log.actor.email
            if name and email:
                user_display = f"{name} ({email})"
            elif name:
                user_display = name
            elif email:
                user_display = email
            else:
                user_display = log.actor.username

        # Format changes to readable text
        changes_text = ""
        if log.changes:
            try:
                # changes is typically a dict or a string depending on auditlog version/configuration
                changes_dict = log.changes if isinstance(log.changes, dict) else json.loads(log.changes)
                formatted_changes = []
                for field, values in changes_dict.items():
                    if isinstance(values, list) and len(values) == 2:
                        old_val = values[0]
                        new_val = values[1]
                        formatted_changes.append(f"{field}: [{old_val}] -> [{new_val}]")
                    else:
                        formatted_changes.append(f"{field}: {values}")
                changes_text = "\n".join(formatted_changes)
            except Exception:
                changes_text = str(log.changes)

        data.append({
            'Data zmiany': timezone.localtime(log.timestamp).strftime('%Y-%m-%d %H:%M') if log.timestamp else "",
            'Użytkownik': user_display,
            'Rodzaj akcji': action_map.get(log.action, str(log.action)),
            'Tabela': log.content_type.name if log.content_type else "Nieznana",
            'Obiekt': log.object_repr,
            'Zmiany (JSON)': changes_text
        })

    df = pd.DataFrame(data, columns=[
        'Data zmiany', 'Użytkownik', 'Rodzaj akcji', 'Tabela', 'Obiekt', 'Zmiany (JSON)'
    ])

    return df
