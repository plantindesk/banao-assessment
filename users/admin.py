from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = (UserAdmin.fieldsets or ()) + (
        ('Additional Information', {'fields': ('role', 'phone_number', 'date_of_birth')}),
    )  # type: ignore[override]

    add_fieldsets = (UserAdmin.add_fieldsets or ()) + (
        ('Additional Information', {'fields': ('role', 'phone_number', 'date_of_birth')}),
    )  # type: ignore[override]

    list_display = (UserAdmin.list_display or ()) + ('role', 'phone_number')  # type: ignore[override]
    
    list_filter = (UserAdmin.list_filter or ()) + ('role',)  # type: ignore[override]

admin.site.register(User, CustomUserAdmin)
