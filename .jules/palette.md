## 2024-11-20 - Adding Accessibility Attributes to Labels
**Learning:** Found that numerous manually rendered Django forms and static form structures across the project were missing the `for` attribute in `<label>` tags, breaking semantic association with inputs and screen reader capabilities.
**Action:** Always ensure that when manually writing out form structures, `for="{{ field.id_for_label }}"` or a static `for="inputId"` is added to `<label>` tags to support programmatic association and improve keyboard/screen-reader accessibility.
