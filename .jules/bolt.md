## 2025-02-18 - Avoid `.first()` on prefetched models
**Learning:** Using `.first()` on a prefetched related manager (like `record.mpk_number.locations.first()`) breaks the Django ORM prefetch cache and triggers an N+1 query.
**Action:** Use `.all()[0] if ...all() else None` to evaluate the prefetched QuerySet in memory.
