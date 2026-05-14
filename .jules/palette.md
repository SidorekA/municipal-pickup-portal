## 2025-01-24 - Screen Reader Compatibility for Icon-Only Buttons
**Learning:** Icon-only buttons using font icons (like Bootstrap Icons) require a two-part approach for screen readers: an `aria-label` on the wrapper `<button>` element to provide context, and an `aria-hidden="true"` attribute on the inner `<i>` tag to prevent screen readers from redundantly announcing the icon's generic name or CSS class.
**Action:** When adding or modifying icon-only buttons, always ensure the parent has an explicit `aria-label` and the child icon is hidden from assistive tech using `aria-hidden="true"`.
