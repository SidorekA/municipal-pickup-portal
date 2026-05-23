## 2026-05-24 - Add ARIA labels to icon-only buttons in top navigation
**Learning:** Many icon-only buttons in the core template lacked accessibility attributes, meaning screen readers would announce raw markup instead of functional names.
**Action:** Always verify that interactive elements relying solely on icons include a descriptive `aria-label` on the parent `<button>` and `aria-hidden="true"` on the nested `<i>` element.
