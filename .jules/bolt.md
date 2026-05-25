## 2024-05-25 - Avoid .first() on prefetch_related managers
**Learning:** Calling `.first()`, `.filter()`, or `.values_list()` on a related manager that was prefetched (e.g., `prefetch_related("mpk_number__locations")`) breaks the prefetch cache and triggers an N+1 query.
**Action:** Always perform in-memory evaluation in Python by using `.all()` (e.g., `locations = obj.locations.all(); first_location = locations[0] if locations else None`).
