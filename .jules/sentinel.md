## 2025-02-20 - Missing Authorization / IDOR on API Endpoint
**Vulnerability:** The `api_get_location_bins` endpoint in `pickups/views.py` returned location details (including contacts and waste bins) without checking if the requester was authenticated or had permission to view the location's MPK.
**Learning:** API endpoints exposing object details by ID need explicit authorization checks matching the user's permissions, even if they aren't directly linked in the UI to unprivileged users.
**Prevention:** Always verify `request.user.is_authenticated` and check permissions (e.g., against the `Permission` model for the associated MPK) before returning data for a requested ID.
