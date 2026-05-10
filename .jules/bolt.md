## 2025-05-10 - Refactoring DB operations with atomic bulk and collections

**Learning:** When generating massive dataset reporting or doing import cycles on large excels, always implement `defaultdict` over filtering iterations and pull keys initially using `select_for_update()` over raw `update_or_create`. Using a set mapping to verify keys and `bulk_create` / `bulk_update` completely eliminates O(n^2) logic flows and N+1 DB operations.

**Action:** Whenever a function loops through DB operations (save, create, delete, match) inside a loop, migrate to `bulk_create` / `bulk_update` arrays and do all dictionary pre-mapping offline before atomic transaction blocks.
