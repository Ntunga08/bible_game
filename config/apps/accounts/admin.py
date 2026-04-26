from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin panel for the extended User model."""

    # Columns shown in the user list
    list_display = [
        'username',
        'email',
        'total_xp',
        'current_streak',
        'highest_level_unlocked',
        'avatar',
        'is_active',
        'date_joined',
    ]

    list_filter = [
        'is_active',
        'is_staff',
        'highest_level_unlocked',
    ]

    search_fields = ['username', 'email']

    ordering = ['-date_joined']

    # Add our custom fields to the user detail page
    fieldsets = UserAdmin.fieldsets + (
        ('Game Profile', {
            'fields': (
                'total_xp',
                'current_streak',
                'longest_streak',
                'last_played_date',
                'highest_level_unlocked',
                'avatar',
            )
        }),
    )