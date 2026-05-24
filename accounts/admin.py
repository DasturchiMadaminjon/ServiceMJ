"""
accounts/admin.py — Foydalanuvchilar va Qurilma Sessiyalari Admin Panel.

Bulk Actions:
  - Tanlangan foydalanuvchilarni faollashtirish / bloklash
  - Tanlangan sessiyalarni tozalash (force logout)
  - Tasdiqlash holatini o'zgartirish
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.utils.translation import ngettext

from .models import CustomUser, DeviceSession


# ──────────────────────────────────────────────────────────────────
# CustomUser Bulk Actions
# ──────────────────────────────────────────────────────────────────

@admin.action(description="✅ Tanlangan foydalanuvchilarni faollashtirish")
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        ngettext(
            '%d foydalanuvchi faollashtirildi.',
            '%d foydalanuvchi faollashtirildi.',
            updated,
        ) % updated,
        messages.SUCCESS,
    )


@admin.action(description="🚫 Tanlangan foydalanuvchilarni bloklash")
def deactivate_users(modeladmin, request, queryset):
    # Superuserlarni bloklashdan saqlash
    updated = queryset.exclude(is_superuser=True).update(is_active=False)
    modeladmin.message_user(
        request,
        ngettext(
            '%d foydalanuvchi bloklandi.',
            '%d foydalanuvchi bloklandi.',
            updated,
        ) % updated,
        messages.WARNING,
    )


@admin.action(description="📱 Tanlangan foydalanuvchilarni tasdiqlash")
def verify_users(modeladmin, request, queryset):
    updated = queryset.update(is_verified=True)
    modeladmin.message_user(
        request,
        '%d foydalanuvchi tasdiqlandi.' % updated,
        messages.SUCCESS,
    )


@admin.action(description="❌ Tanlangan foydalanuvchilarni tasdiqdan chiqarish")
def unverify_users(modeladmin, request, queryset):
    updated = queryset.update(is_verified=False)
    modeladmin.message_user(
        request,
        '%d foydalanuvchi tasdiqdan chiqarildi.' % updated,
        messages.WARNING,
    )


@admin.action(description="🔑 Tanlangan foydalanuvchilarni 'client' roliga o'tkazish")
def set_role_client(modeladmin, request, queryset):
    updated = queryset.exclude(is_superuser=True).update(role='client')
    modeladmin.message_user(request, '%d foydalanuvchi "mijoz" roliga o\'tkazildi.' % updated, messages.SUCCESS)


@admin.action(description="🛠️ Tanlangan foydalanuvchilarni 'provider' roliga o'tkazish")
def set_role_provider(modeladmin, request, queryset):
    updated = queryset.exclude(is_superuser=True).update(role='provider')
    modeladmin.message_user(request, '%d foydalanuvchi "usta" roliga o\'tkazildi.' % updated, messages.SUCCESS)


# ──────────────────────────────────────────────────────────────────
# DeviceSession Bulk Actions
# ──────────────────────────────────────────────────────────────────

@admin.action(description="🗑️ Tanlangan sessiyalarni o'chirish (Force Logout)")
def clear_sessions(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(
        request,
        '%d sessiya o\'chirildi (foydalanuvchilar tizimdan chiqarildi).' % count,
        messages.SUCCESS,
    )


# ──────────────────────────────────────────────────────────────────
# Admin Klasslari
# ──────────────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'role', 'phone_number', 'is_verified', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_verified', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering      = ('-date_joined',)
    fieldsets     = UserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {'fields': ('role', 'phone_number', 'is_verified', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Qo'shimcha", {'fields': ('role', 'phone_number')}),
    )
    actions = [
        activate_users,
        deactivate_users,
        verify_users,
        unverify_users,
        set_role_client,
        set_role_provider,
        # Django built-in: 'delete_selected' ham avtomatik mavjud
    ]


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    """Qurilma sessiyalarini admin panelda ko'rish va boshqarish."""
    list_display    = ('user', 'device_name', 'ip_address', 'last_active', 'created_at')
    list_filter     = ('created_at',)
    search_fields   = ('user__username', 'device_name', 'ip_address')
    readonly_fields = ('refresh_jti', 'device_name', 'ip_address', 'last_active', 'created_at')
    ordering        = ('-last_active',)
    actions         = [clear_sessions]

    def has_add_permission(self, request):
        return False  # Sessiyalar faqat login orqali yaratiladi
