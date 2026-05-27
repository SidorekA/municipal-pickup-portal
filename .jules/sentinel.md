## 2024-05-18 - Missing IDOR prevention and improper API authentication

**Vulnerability:**
The API endpoint `api_get_pickup_dates` used the `@login_required` decorator, which incorrectly triggered a 302 redirect to an HTML login page for unauthenticated users instead of returning a 403 JSON response. Additionally, the endpoint did not check if the authenticated user had permission (authorization) to access the specific `location_id` passed as a parameter, leading to an IDOR (Insecure Direct Object Reference) vulnerability.

**Learning:**
In this Django codebase, API endpoints returning `JsonResponse` should not use decorators like `@login_required`, as this breaks frontend JavaScript clients expecting JSON. Furthermore, simply checking authentication is insufficient for endpoints taking identifiers (like `location_id`); we must always verify authorization to ensure the user has access to that specific resource via `Permission.objects`.

**Prevention:**
Always manually check `request.user.is_authenticated` within JSON API views and return a 403 `JsonResponse` on failure. For endpoints receiving resource IDs, retrieve the object and explicitly verify permissions (e.g., checking `Permission.objects.filter(...)`) before returning data.
