## 2024-05-24 - Avoiding N+1 Queries on Prefetched Related Managers
**Learning:** Calling `.first()`, `.filter()`, or `.values_list()` on a related manager (e.g., `locations.first()`) that has been retrieved using `prefetch_related` breaks the Django ORM cache and forces a new database query. When done inside a loop, this leads to an N+1 query performance bottleneck.
**Action:** Always evaluate the prefetched manager in Python memory using `.all()` (e.g., `locations = obj.related.all()`, then access `locations[0] if locations else None`) instead of executing ORM methods that hit the database.
