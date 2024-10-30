from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from . import models


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups'
            ),
        }),
    )


class GroupAdmin(admin.ModelAdmin):
    """Define the admin pages for groups."""
    list_display = ['name']
    search_fields = ['name']
    filter_horizontal = ['members']


class WorkoutAdmin(admin.ModelAdmin):
    """Define the admin pages for workouts."""
    list_display = ['title', 'user', 'date']
    search_fields = ['title', 'user__email']
    list_filter = ['date', 'user']


class MessageAdmin(admin.ModelAdmin):
    """Define the admin pages for messages."""
    list_display = ['content', 'group', 'sender', 'timestamp']
    search_fields = ['content', 'group__name', 'sender__email']
    list_filter = ['timestamp']


class CommentAdmin(admin.ModelAdmin):
    """Define the admin pages for comments."""
    list_display = ['text', 'workout', 'author', 'created_at']
    search_fields = ['text', 'workout__title', 'author__email']
    list_filter = ['created_at']


# Register models with the admin site
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Workout, WorkoutAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.Comment, CommentAdmin)
