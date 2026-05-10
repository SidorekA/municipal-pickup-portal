# scheduling/services.py

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from waste.models import WasteFractionType

WARSAW_TZ = ZoneInfo("Europe/Warsaw")
CUTOFF_HOUR = 12


def get_next_pickup_date(
    fraction_type: "WasteFractionType",
    submitted_at: datetime | None = None,
) -> date | None:
    """
    Zwraca najbliższą możliwą datę odbioru dla danego typu frakcji.

    Zasada: zgłoszenie musi wpłynąć PRZED 12:00 dnia poprzedzającego odbiór.

    Przykłady dla frakcji odbieranej w Wt, Pt:
        pn 11:00  →  wtorek  (przed 12:00 → łapie najbliższy dzień)
        pn 12:30  →  piątek  (po 12:00 → wtorek odpada)
        wt 08:00  →  piątek  (wtorek jest dzisiaj, nie "następny")
        pt 11:59  →  wtorek przyszłego tygodnia

    Args:
        fraction_type: instancja WasteFractionType z prefetch schedules
        submitted_at:  moment zgłoszenia (naive → przyjmuje Warsaw TZ);
                       None → teraz

    Returns:
        date odbioru lub None gdy brak aktywnych wpisów w harmonogramie
    """
    if submitted_at is None:
        submitted_at = datetime.now(tz=WARSAW_TZ)
    elif submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=WARSAW_TZ)

    # ⚡ Bolt: We use list comprehension over .all() rather than .filter() or .values_list()
    # to leverage prefetch_related and avoid breaking the cache, resolving an N+1 query issue.
    pickup_days: set[int] = set(
        schedule.day_of_week for schedule in fraction_type.schedules.all() if schedule.active
    )

    if not pickup_days:
        return None

    today = submitted_at.date()

    one_day = timedelta(days=1)
    day_before = today
    candidate = today + one_day

    for _ in range(1, 15):
        if candidate.isoweekday() in pickup_days:
            deadline = datetime(
                day_before.year,
                day_before.month,
                day_before.day,
                CUTOFF_HOUR, 0, 0,
                tzinfo=WARSAW_TZ,
            )

            if submitted_at < deadline:
                return candidate

        day_before = candidate
        candidate += one_day

    return None