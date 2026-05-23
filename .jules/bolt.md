## 2024-05-18 - [Optimized Dashboard N+1 Queries]
**Learning:** Found N+1 queries in the core home_view loop caused by `.all()` hitting fraction_type__schedules because the `waste_bins__waste_fraction__fraction_type__schedules` were not deeply prefetched.
**Action:** Adding `__schedules` to the prefetch_related statement for `waste_bins__waste_fraction__fraction_type` prevents thousands of extra queries for `CollectionSchedule`.
