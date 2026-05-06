import io
from openpyxl import Workbook
from openpyxl.styles import Font

FRACTION_COLUMNS = [
    ('zmieszane_1100', 'zmieszane', 1100),
    ('makulatura_1100', 'makulatura', 1100),
    ('plastik_1100', 'plastik', 1100),
    ('plastik_240', 'plastik', 240),
    ('szklo_1100', 'szkło', 1100),
    ('szklo_240', 'szkło', 240),
    ('szklo_120', 'szkło', 120),
    ('bio', 'bio', None),
    ('baterie', 'baterie', None),
]

HEADERS = [
    'numer_mpk', 'nazwa_komorki_organizacyjnej', 'nazwa_obiektu',
    'lokalizacja', 'zmieszane_1100', 'makulatura_1100', 'plastik_1100',
    'plastik_240', 'szklo_1100', 'szklo_240', 'szklo_120', 'bio',
    'baterie', 'numer_telefonu', 'Utworzony', 'Utworzone przez',
    'informacje_dodatkowe',
]


def _dopasuj_frakcje(waste_bin, keyword: str, capacity: int | None) -> bool:
    """Sprawdza czy pojemnik pasuje do danej kolumny Excela."""
    name_ok = keyword.lower() in waste_bin.waste_fraction.fraction_type.name.lower()
    if capacity is not None:
        return name_ok and waste_bin.waste_fraction.capacity == capacity
    return name_ok


def generate_pickup_excel(pickup) -> bytes:
    """Generuje Excel dla zgłoszenia i zwraca go jako bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = "zgloszenia_odpadow_do_wysylania"

    for col_idx, header in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    waste_bins = list(
        pickup.waste_bins.select_related('waste_fraction__fraction_type').all()
    )

    location = pickup.location
    row = {
        'numer_mpk': pickup.mpk_number.mpk_number,
        'nazwa_komorki_organizacyjnej': location.org_unit_name,
        'nazwa_obiektu': location.obj_name,
        'lokalizacja': location.localization,
        'numer_telefonu': getattr(pickup, 'contact_phone', ''),
        'Utworzony': pickup.reported_at.strftime('%Y-%m-%d %H:%M'),
        'Utworzone przez': pickup.reporter.get_full_name() or str(pickup.reporter),
        'informacje_dodatkowe': getattr(pickup, 'note', '') or '',
    }

    for col_name, keyword, capacity in FRACTION_COLUMNS:
        quantity = next(
            (wb_item.quantity for wb_item in waste_bins
             if _dopasuj_frakcje(wb_item, keyword, capacity)),
            0
        )
        row[col_name] = quantity if quantity > 0 else ''

    ws.append([row.get(h, '') for h in HEADERS])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max(max_len + 2, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()