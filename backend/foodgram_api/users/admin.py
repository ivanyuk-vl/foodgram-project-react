from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields': ('username', 'email', 'first_name',
                   'last_name', 'password1', 'password2')
    }),)
