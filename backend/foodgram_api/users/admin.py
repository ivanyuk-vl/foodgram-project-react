from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields': ('username', 'email', 'first_name',
                   'last_name', 'password1', 'password2')
    }),)


admin.site.register(Subscribe)
