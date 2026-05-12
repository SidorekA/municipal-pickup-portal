## 2026-05-12 - Topbar Accessibility Enhancement
**Learning:** Critical topbar interactive elements (Logout, Profile, Notifications) were missing ARIA labels and screen-reader-only context, which is a common pattern for icon-only buttons or avatars.
**Action:** Always ensure topbar and navigation icons/avatars have `aria-label`, decorative elements use `aria-hidden="true"`, and badge counts include `.visually-hidden` text to provide context for screen readers.
