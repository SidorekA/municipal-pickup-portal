## 2024-11-20 - [Aria labels on base template buttons]
**Learning:** Icon-only buttons used across the app layout (like sidebar toggle, logout, notifications) lacked context for screen readers in `templates/base.html`, missing both `aria-label`s and `title`s, which created navigational blind spots.
**Action:** Ensure that all top-bar and globally used icon-only components include `aria-label` with descriptive action verbs and `aria-hidden="true"` on the icon itself to prevent redundant readings.
