## 2024-05-16 - Add ARIA labels to icon-only buttons
**Learning:** Found multiple icon-only buttons across the application (sidebar toggles, notification read status, logout, and pagination controls) lacking `aria-label` and `aria-hidden="true"` on their respective icons, which negatively impacts screen reader users.
**Action:** When adding icon-only interactive elements in Django templates (especially Bootstrap Icons), always include a descriptive `aria-label` on the `<button>` and `aria-hidden="true"` on the internal `<i>` tag.
