## 2025-05-24 - IDOR in API endpoints due to lack of authorization check
**Vulnerability:** The API endpoint `api_get_pickup_dates` returned sensitive pickup dates for a given location ID, and was missing explicit authorization checks against the user permissions.
**Learning:** Returning `@login_required` is not enough for securing APIs; JSON endpoints require returning 403 on unauthenticated, but more critically, they require custom object-level permission verification matching user-to-object relation (`Permission` table).
**Prevention:** Always verify `request.user.is_authenticated` manually and explicitly check `Permission.objects.filter(user=request.user, mpk_number=location.mpk_number, active=True).exists()` to prevent IDOR in API views.
