## 2024-05-20 - IDOR in API endpoints

**Vulnerability:** The `api_get_pickup_dates` endpoint was vulnerable to Insecure Direct Object Reference (IDOR). It took a `location_id` directly without verifying that the authenticated user actually had permission (`Permission.objects.filter(...)`) for the corresponding `mpk_number`. This allowed any authenticated user to iterate through locations and retrieve pickup dates.

**Learning:** Just checking if a user is authenticated (`@login_required`) is insufficient for endpoints that accept object IDs (like `location_id`). A second layer of authorization check, usually tying the object back to the requesting user's explicit permissions, is necessary.

**Prevention:** Always verify both authentication and authorization. When resolving an object ID passed via an API parameter, explicitly check if the currently authenticated user (`request.user`) is permitted to access that specific object, typically by checking against permission models or user-assigned constraints.
