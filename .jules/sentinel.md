## 2024-05-18 - Prevent IDOR and HTML Redirects in API Endpoints

**Vulnerability:** The `api_get_pickup_dates` API endpoint was vulnerable to Insecure Direct Object Reference (IDOR) because it failed to check if the user had authorization for the requested `Location`'s MPK. Additionally, the endpoint used Django's standard `@login_required` decorator, which improperly responded with a 302 redirect to an HTML login page instead of a JSON response when unauthenticated requests were made.

**Learning:** When creating API endpoints that return JSON, Django's standard decorators like `@login_required` or `@staff_member_required` break frontend clients because they trigger an HTML redirect. Additionally, ensuring a user is authenticated is insufficient; endpoints interacting with models (e.g., `Location`) must check if the user has authorization for the related object via the `Permission` model.

**Prevention:** Manually verify `request.user.is_authenticated` inside the view and return a `JsonResponse` with a 403 status code on failure. Implement authorization checks against associated MPK models (e.g., `Permission.objects.filter(user=request.user, mpk_number=..., active=True).exists()`) and return a 403 `JsonResponse` if the check fails.
