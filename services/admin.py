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
    list_display  = ('icon_badge', 'name', 'parent', 'skills_count', 'providers_count')
    search_fields = ('name',)
    list_filter   = ('parent',)
    ordering      = ('name',)

    def icon_badge(self, obj):
        icon = obj.icon or '📁'
        return format_html('<span style="font-size:18px;margin-right:6px">{}</span>', icon)
    icon_badge.short_description = "Ikonka"

    def skills_count(self, obj):
        count = obj.skills.count()
        return format_html('<b>{}</b> ta ko\'nikma', count)
    skills_count.short_description = "Ko'nikmalar"

    def providers_count(self, obj):
        count = ProviderProfile.objects.filter(skills__category=obj, is_active=True).distinct().count()
        return format_html('<span style="background:#e0e7ff;color:#3730a3;padding:3px 8px;border-radius:10px;font-weight:600">{} usta</span>', count)
    providers_count.short_description = "Faol ustalar soni"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category_badge', 'providers_count')
    search_fields = ('name', 'category__name')
    list_filter   = ('category',)
    ordering      = ('category__name', 'name')

    def category_badge(self, obj):
        if obj.category:
            return format_html('<span style="background:#f3f4f6;padding:3px 8px;border-radius:8px;font-weight:500">{} {}</span>', obj.category.icon or '', obj.category.name)
        return format_html('<span style="color:#9ca3af">—</span>')
    category_badge.short_description = "Kategoriya"

    def providers_count(self, obj):
        count = obj.providers.filter(is_active=True).count()
        return format_html('<span style="color:#4f46e5;font-weight:600">{} usta</span>', count)
    providers_count.short_description = "Ustalar"


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display       = ('user_info', 'rating_display', 'total_reviews', 'skills_preview', 'hourly_rate_display', 'experience_badge', 'status_badge')
    list_filter        = ('is_active', 'skills__category')
    search_fields      = ('user__username', 'user__phone_number', 'bio', 'skills__name')
    readonly_fields    = ('rating',)
    filter_horizontal  = ('skills',)
    list_per_page      = 25
    actions = [
        activate_providers,
        deactivate_providers,
        reset_ratings,
    ]

    def user_info(self, obj):
        phone = obj.user.phone_number or ''
        return format_html(
            '<div><b>{}</b><br><small style="color:#6b7280">{}</small></div>',
            obj.user.username, phone
        )
    user_info.short_description = "Usta"

    def rating_display(self, obj):
        r = float(obj.rating or 0)
        return format_html(
            '<span style="background:#fef3c7;color:#92400e;padding:3px 8px;border-radius:10px;font-weight:700">⭐ {:.1f}</span>',
            r
        )
    rating_display.short_description = "Reyting"

    def total_reviews(self, obj):
        count = obj.user.received_reviews.count()
        return format_html('<b>{}</b> sharh', count)
    total_reviews.short_description = "Sharhlar"

    def skills_preview(self, obj):
        skills = obj.skills.all()[:3]
        if not skills:
            return format_html('<span style="color:#9ca3af">—</span>')
        pills = "".join(f'<span style="background:#e0e7ff;color:#3730a3;padding:2px 6px;border-radius:6px;margin-right:4px;font-size:11px">{s.name}</span>' for s in skills)
        if obj.skills.count() > 3:
            pills += f'<span style="color:#6b7280;font-size:11px">+{obj.skills.count()-3}</span>'
        return format_html(pills)
    skills_preview.short_description = "Ko'nikmalar"

    def hourly_rate_display(self, obj):
        if not obj.hourly_rate:
            return format_html('<span style="color:#9ca3af">Kelishuv</span>')
        return format_html('<b>{:,.0f}</b> so\'m/soat', float(obj.hourly_rate))
    hourly_rate_display.short_description = "Tarif"

    def experience_badge(self, obj):
        return format_html('<span>📅 {} yil</span>', obj.experience_years)
    experience_badge.short_description = "Tajriba"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background:#ecfdf5;color:#059669;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600">🟢 Faol</span>')
        return format_html('<span style="background:#fee2e2;color:#dc2626;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600">🔴 Nofaol</span>')
    status_badge.short_description = "Holat"


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display  = ('thumbnail_display', 'title', 'provider', 'created_at')
    search_fields = ('title', 'provider__user__username')
    list_filter   = ('created_at',)
    ordering      = ('-created_at',)

    def thumbnail_display(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;border-radius:8px;object-fit:cover;border:1px solid #e2e8f0;" />',
                obj.image.url
            )
        return format_html('<div style="width:48px;height:48px;border-radius:8px;background:#f3f4f6;display:flex;align-items:center;justify-content:center;color:#9ca3af;font-size:20px">🖼️</div>')
    thumbnail_display.short_description = "Rasm"

