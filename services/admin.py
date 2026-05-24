"""
services/admin.py — Kategoriya, Ko'nikma, Usta Profili va Portfolio Admin Panel.

Bulk Actions:
  - Kategoriyalarni tanlash va o'chirish
  - Usta profillarini faollashtirish / o'chirish
  - Ko'nikmalarni tanlash va o'chirish
  - Portfolio elementlarini tanlash va o'chirish
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import Category, Skill, ProviderProfile, PortfolioItem


# ──────────────────────────────────────────────────────────────────
# ProviderProfile Bulk Actions
# ──────────────────────────────────────────────────────────────────

@admin.action(description="✅ Tanlangan usta profillarini faollashtirish")
def activate_providers(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        '%d usta profili faollashtirildi.' % updated,
        messages.SUCCESS,
    )


@admin.action(description="🚫 Tanlangan usta profillarini o'chirish (deactivate)")
def deactivate_providers(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        '%d usta profili o\'chirildi (deactivate).' % updated,
        messages.WARNING,
    )


@admin.action(description="🔄 Reytingni nolga qaytarish")
def reset_ratings(modeladmin, request, queryset):
    updated = queryset.update(rating=0.0)
    modeladmin.message_user(
        request,
        '%d usta reytingi nolga qaytarildi.' % updated,
        messages.WARNING,
    )


# ──────────────────────────────────────────────────────────────────
# Admin Klasslari
# ──────────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'parent', 'icon', 'skill_count')
    search_fields = ('name',)
    list_filter   = ('parent',)
    # Django built-in 'delete_selected' avtomatik mavjud

    def skill_count(self, obj):
        return obj.skills.count()
    skill_count.short_description = "Ko'nikmalar soni"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category')
    search_fields = ('name',)
    list_filter   = ('category',)
    # Django built-in 'delete_selected' avtomatik mavjud


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display       = ('user', 'rating', 'total_reviews', 'experience_years', 'is_active', 'hourly_rate')
    list_filter        = ('is_active',)
    search_fields      = ('user__username', 'bio')
    readonly_fields    = ('rating',)
    filter_horizontal  = ('skills',)
    list_per_page      = 25
    actions = [
        activate_providers,
        deactivate_providers,
        reset_ratings,
    ]

    def total_reviews(self, obj):
        """Ustaning jami sharhlari sonini hisoblaydi."""
        return obj.user.received_reviews.count()
    total_reviews.short_description = "Sharhlar"


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display  = ('title', 'provider', 'has_image', 'created_at')
    search_fields = ('title', 'provider__user__username')
    list_filter   = ('created_at',)
    # Django built-in 'delete_selected' avtomatik mavjud

    def has_image(self, obj):
        if obj.image:
            return format_html('<span style="color:green">✅ Bor</span>')
        return format_html('<span style="color:gray">—</span>')
    has_image.short_description = "Rasm"
