# users/admin.py
from django.contrib import admin
# from .models import Permission, UserProfile

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ("user", "phone", "department", "created_at", "updated_at")
#     search_fields = ("user__username", "user__email", "phone", "department")

# @admin.register(Permission)
# class PermissionAdmin(admin.ModelAdmin):
#     list_display = ("user", "location", "role", "active", "granted_by", "created_at")
#     list_filter = ("role", "active")
#     search_fields = ("user__username", "location__name", "location__mpk_number__number")