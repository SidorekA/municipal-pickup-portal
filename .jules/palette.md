## 2026-05-21 - [Accessible Icon-Only Controls in WasteFlow Design System]
**Learning:** The custom 'WasteFlow' topbar components (e.g., `wf-notif-btn`, `btn-sidebar-toggle`) and system actions (like logout) systematically rely on visual Bootstrap Icons without accessible labels, causing screen readers to miss primary navigation actions.
**Action:** When implementing icon-only buttons using the custom `wf-` classes, always explicitly add an `aria-label` with a descriptive action verb to the button and `aria-hidden="true"` to the inner `<i>` tag to prevent redundant screen reader readings.
