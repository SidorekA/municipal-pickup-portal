## 2025-05-10 - Refactoring DB operations with atomic bulk and collections

**Learning:** When generating massive dataset reporting or doing import cycles on large excels, always implement `defaultdict` over filtering iterations and pull keys initially using `select_for_update()` over raw `update_or_create`. Using a set mapping to verify keys and `bulk_create` / `bulk_update` completely eliminates O(n^2) logic flows and N+1 DB operations.

**Action:** Whenever a function loops through DB operations (save, create, delete, match) inside a loop, migrate to `bulk_create` / `bulk_update` arrays and do all dictionary pre-mapping offline before atomic transaction blocks.
## 2025-05-15 - Refactoring linear lookups in report generation

**Learning:** When looping over thousands of database records and cross-referencing them against another set of database objects, executing a linear lookup in the list of objects for every record has `O(N*M)` complexity. In our `generate_mpk_cost_report` we were parsing over thousands of `SummaryCollectionSchedule` records and linearly searching over `WasteCost` list.

**Action:** Whenever cross-referencing collections during massive report generation or data exports, pre-group related fields using `defaultdict` (such as `defaultdict(list)` grouped by `fraction_id`). This refactoring changes the linear search complexity to `O(N*K)` lookup and massively optimizes the loop execution time from `0.10s` to `0.009s` in worst case scenarios.
