# users/admin.py
from django.contrib import admin
from .models import UserProfile, Permission, Coordinator


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department_short', 'department_name', 'phone']
    search_fields = ['user__username', 'department_name']
    ordering = ['department_short']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'mpk_number', 'role', 'active', 'granted_by']
    list_filter = ['role', 'active']
    search_fields = ['user__username', 'mpk_number__mpk_number']
    ordering = ['mpk_number__mpk_number']


@admin.register(Coordinator)
class CoordinatorAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'active']
    list_filter = ['active']
    search_fields = ['user__username', 'location__obj_name']
    ordering = ['location__obj_name']