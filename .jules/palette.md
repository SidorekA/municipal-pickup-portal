## 2024-05-17 - Added aria-labels and aria-hidden to icon-only buttons
**Learning:** Found a common pattern of missing ARIA labels on icon-only buttons (`sidebar toggle`, `logout`, etc.). This causes screen readers to announce nothing or something confusing.
**Action:** When adding icon-only buttons, I must add a descriptive `aria-label` to the `<button>` element and `aria-hidden="true"` to the inner `<i>` tag to improve keyboard and screen reader accessibility.
