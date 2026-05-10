1. **Fix sequential unlocking**:
   - Remove `disabled="disabled"` from `pickup_form.html` for `location` and `contact_phone`.
   - In `dynamic_bins.js`, set `locationSelect.disabled = true` and `phoneSelect.disabled = true` initially, ONLY IF they don't have a pre-selected value.
   - Ensure `phoneSelect.disabled = false` happens not only when `data.contacts` is present, but unconditionally after location is selected (since there might be "Mój numer" or other options available).

2. **Fix form state reset on backend validation**:
   - When the backend returns validation errors, the dynamic fields (bins, phone) are lost because they are recreated via API.
   - Inject `window.PREVIOUS_POST_DATA` in `pickup_form.html` containing the `bin_X` values and `contact_phone` from `request.POST`.
   - In `dynamic_bins.js`, when rendering bins, check if `window.PREVIOUS_POST_DATA` has a value for `bin_${bin.fraction_id}` and set it as the default value instead of `0`.
   - After populating `phoneSelect` choices, set its value to `window.PREVIOUS_POST_DATA["contact_phone"]` if available.

3. **Improve Client-Side Validation**:
   - If `binInputs.length === 0`, we shouldn't submit if the user is supposed to select bins. The current logic allows submit if `binInputs.length === 0`.
   - Highlight the bins container appropriately.

4. **Verify**:
   - Verify that fields unlock sequentially.
   - Verify that submitting with errors preserves values.
