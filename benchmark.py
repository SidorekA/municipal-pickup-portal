import timeit
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

WARSAW_TZ = ZoneInfo("Europe/Warsaw")
CUTOFF_HOUR = 12

def original_loop(pickup_days, submitted_at):
    today = submitted_at.date()
    for delta in range(1, 15):
        candidate = today + timedelta(days=delta)

        if candidate.isoweekday() not in pickup_days:
            continue

        day_before = candidate - timedelta(days=1)
        deadline = datetime(
            day_before.year,
            day_before.month,
            day_before.day,
            CUTOFF_HOUR, 0, 0,
            tzinfo=WARSAW_TZ,
        )

        if submitted_at < deadline:
            return candidate

    return None

def optimized_loop(pickup_days, submitted_at):
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

# Test case where it goes up to max iterations
pickup_days = {7} # Sunday
submitted_at = datetime(2023, 10, 16, 15, 0, 0, tzinfo=WARSAW_TZ) # Monday 15:00

print("Original:", timeit.timeit(lambda: original_loop(pickup_days, submitted_at), number=10000))
print("Optimized:", timeit.timeit(lambda: optimized_loop(pickup_days, submitted_at), number=10000))
