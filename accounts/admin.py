from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DeviceSession


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'role', 'phone_number', 'is_verified', 'is_active')
    list_filter   = ('role', 'is_verified', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets     = UserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {'fields': ('role', 'phone_number', 'is_verified', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Qo'shimcha", {'fields': ('role', 'phone_number')}),
    )


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    """Qurilma sessiyalarini admin panelda ko'rish va boshqarish."""
    list_display   = ('user', 'device_name', 'ip_address', 'last_active', 'created_at')
    list_filter    = ('created_at',)
    search_fields  = ('user__username', 'device_name', 'ip_address')
    readonly_fields = ('refresh_jti', 'device_name', 'ip_address', 'last_active', 'created_at')
    ordering       = ('-last_active',)

    def has_add_permission(self, request):
        return False  # Sessiyalar faqat login orqali yaratiladi
