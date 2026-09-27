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

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.utils.html import format_html
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
    list_display  = (
        'avatar_thumbnail',
        'username',
        'role_badge',
        'phone_display',
        'verification_badge',
        'status_badge',
        'date_joined',
    )
    list_display_links = ('avatar_thumbnail', 'username')
    list_filter   = ('role', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    ordering      = ('-date_joined',)
    date_hierarchy = 'date_joined'
    list_per_page = 25
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
    ]

    def avatar_thumbnail(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid #e2e8f0;" />',
                obj.avatar.url
            )
        initial = (obj.username[:1] or 'U').upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg, #6366f1, #8b5cf6);'
            'color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">{}</div>',
            initial
        )
    avatar_thumbnail.short_description = "Avatar"

    def role_badge(self, obj):
        roles = {
            'provider': ('#4f46e5', '#eef2ff', '🛠️ Usta'),
            'client':   ('#059669', '#ecfdf5', '👤 Mijoz'),
            'admin':    ('#dc2626', '#fef2f2', '👑 Admin'),
        }
        color, bg, label = roles.get(obj.role, ('#4b5563', '#f3f4f6', obj.role))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;border-radius:12px;font-size:12px;font-weight:600;display:inline-block;">{}</span>',
            bg, color, label
        )
    role_badge.short_description = "Rol"

    def phone_display(self, obj):
        if not obj.phone_number:
            return format_html('<span style="color:#9ca3af">—</span>')
        p = obj.phone_number
        if len(p) == 12:
            formatted = f"+{p[:3]} ({p[3:5]}) {p[5:8]}-{p[8:10]}-{p[10:]}"
        else:
            formatted = p
        return format_html('<span style="font-family:monospace;font-size:12px;font-weight:500">{}</span>', formatted)
    phone_display.short_description = "Telefon"

    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="background:#ecfdf5;color:#059669;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600">✅ Tasdiqlangan</span>')
        return format_html('<span style="background:#fffbeb;color:#d97706;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600">⏳ Kutilmoqda</span>')
    verification_badge.short_description = "SMS Tasdiq"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#059669;font-weight:600;font-size:12px">🟢 Faol</span>')
        return format_html('<span style="background:#fee2e2;color:#dc2626;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600">🚫 Bloklangan</span>')
    status_badge.short_description = "Holat"


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display    = ('user', 'device_name', 'ip_address', 'last_active', 'created_at')
    list_filter     = ('created_at',)
    search_fields   = ('user__username', 'device_name', 'ip_address')
    readonly_fields = ('refresh_jti', 'device_name', 'ip_address', 'last_active', 'created_at')
    ordering        = ('-last_active',)
    actions         = [clear_sessions]

    def has_add_permission(self, request):
        return False

