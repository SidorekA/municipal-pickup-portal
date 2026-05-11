## 2025-05-10 - Refactoring DB operations with atomic bulk and collections

**Learning:** When generating massive dataset reporting or doing import cycles on large excels, always implement `defaultdict` over filtering iterations and pull keys initially using `select_for_update()` over raw `update_or_create`. Using a set mapping to verify keys and `bulk_create` / `bulk_update` completely eliminates O(n^2) logic flows and N+1 DB operations.

**Action:** Whenever a function loops through DB operations (save, create, delete, match) inside a loop, migrate to `bulk_create` / `bulk_update` arrays and do all dictionary pre-mapping offline before atomic transaction blocks.

## 2025-05-10 - O(N^2) Cost Lookup Optimization

**Learning:** In reporting functions that iterate over datasets to fetch related historical prices (e.g. `generate_mpk_cost_report`), repeatedly iterating over all cached costs per row results in an O(M * N) bottleneck.

**Action:** Pre-group the fetched `all_costs` into a `defaultdict(list)` indexed by the joining key (`waste_fraction_id` in this case), and lookup costs strictly for that subset. This reduces the time complexity effectively to O(N).
