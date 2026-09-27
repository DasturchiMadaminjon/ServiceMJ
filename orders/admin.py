"""
orders/admin.py — Xizmat So'rovlari va Sharhlar Admin Panel.

Bulk Actions:
  - Tanlangan so'rovlarni bekor qilish
  - Tanlangan so'rovlarni arxivlash (completed)
  - Tanlangan so'rovlarni "pending" ga qaytarish
  - Tanlangan sharhlarni tanlash va o'chirish
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import ServiceRequest, Review


# ──────────────────────────────────────────────────────────────────
# ServiceRequest Bulk Actions
# ──────────────────────────────────────────────────────────────────

@admin.action(description="❌ Tanlangan so'rovlarni bekor qilish (cancelled)")
def cancel_requests(modeladmin, request, queryset):
    """Faqat 'pending' va 'accepted' holatdagilarni bekor qilish mumkin."""
    cancellable = queryset.filter(status__in=['pending', 'accepted', 'in_progress'])
    count = cancellable.count()
    cancellable.update(status='cancelled')
    modeladmin.message_user(
        request,
        '%d ta so\'rov bekor qilindi.' % count,
        messages.WARNING,
    )


@admin.action(description="✅ Tanlangan so'rovlarni yakunlash (completed)")
def complete_requests(modeladmin, request, queryset):
    """In-progress so'rovlarni tugallangan deb belgilash."""
    completable = queryset.filter(status='in_progress')
    count = completable.count()
    completable.update(status='completed')
    modeladmin.message_user(
        request,
        '%d ta so\'rov yakunlangan deb belgilandi.' % count,
        messages.SUCCESS,
    )


@admin.action(description="🔄 Tanlangan so'rovlarni 'kutilmoqda' ga qaytarish")
def reset_to_pending(modeladmin, request, queryset):
    """Faqat bekor qilingan so'rovlarni pending ga qaytarish."""
    resettable = queryset.filter(status='cancelled')
    count = resettable.count()
    resettable.update(status='pending', provider=None)
    modeladmin.message_user(
        request,
        '%d ta so\'rov qayta "kutilmoqda" holatiga o\'tkazildi.' % count,
        messages.SUCCESS,
    )


@admin.action(description="🛠️ Tanlangan so'rovlarni 'jarayonda' ga o'tkazish")
def mark_in_progress(modeladmin, request, queryset):
    in_progress = queryset.filter(status='accepted')
    count = in_progress.count()
    in_progress.update(status='in_progress')
    modeladmin.message_user(
        request,
        '%d ta so\'rov "jarayonda" holatiga o\'tkazildi.' % count,
        messages.SUCCESS,
    )


# ──────────────────────────────────────────────────────────────────
# Admin Klasslari
# ──────────────────────────────────────────────────────────────────

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display         = ('id', 'customer_info', 'category_badge', 'status_badge', 'provider_info', 'budget_display', 'created_at')
    list_display_links   = ('id', 'customer_info')
    list_filter          = ('status', 'category', 'currency', 'created_at')
    search_fields        = ('customer__username', 'customer__phone_number', 'provider__username', 'description', 'address')
    readonly_fields      = ('created_at', 'updated_at')
    list_per_page        = 25
    date_hierarchy       = 'created_at'
    ordering             = ('-created_at',)
    actions = [
        cancel_requests,
        complete_requests,
        reset_to_pending,
        mark_in_progress,
    ]

    def customer_info(self, obj):
        phone = obj.customer.phone_number or ''
        return format_html(
            '<div><b>{}</b><br><small style="color:#6b7280">{}</small></div>',
            obj.customer.username, phone
        )
    customer_info.short_description = "Mijoz"

    def provider_info(self, obj):
        if obj.provider:
            phone = obj.provider.phone_number or ''
            return format_html(
                '<div><b>🛠️ {}</b><br><small style="color:#6b7280">{}</small></div>',
                obj.provider.username, phone
            )
        return format_html('<span style="color:#9ca3af;font-style:italic">Biriktirilmagan</span>')
    provider_info.short_description = "Usta"

    def category_badge(self, obj):
        if obj.category:
            return format_html('<span style="background:#f3f4f6;padding:3px 8px;border-radius:8px;font-weight:500">{} {}</span>', obj.category.icon or '', obj.category.name)
        return format_html('<span style="color:#9ca3af">—</span>')
    category_badge.short_description = "Kategoriya"

    def budget_display(self, obj):
        if not obj.budget:
            return format_html('<span style="color:#9ca3af">Kelishuv</span>')
        curr = "so'm" if obj.currency == 'UZS' else "$"
        return format_html('<b>{:,.0f}</b> <small>{}</small>', float(obj.budget), curr)
    budget_display.short_description = "Byudjet"

    def status_badge(self, obj):
        """Status uchun rangli zamonaviy badge ko'rinishi."""
        colors = {
            'pending':     ('#fffbeb', '#b45309', '⏳ Kutilmoqda'),
            'accepted':    ('#eff6ff', '#1d4ed8', '🤝 Qabul qilindi'),
            'in_progress': ('#f5f3ff', '#6d28d9', '🔧 Jarayonda'),
            'completed':   ('#ecfdf5', '#047857', '✅ Tugallandi'),
            'cancelled':   ('#fef2f2', '#b91c1c', '❌ Bekor qilindi'),
        }
        bg, text_color, label = colors.get(obj.status, ('#f3f4f6', '#4b5563', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:12px;font-size:12px;font-weight:600;display:inline-block">{}</span>',
            bg, text_color, label
        )
    status_badge.short_description = "Holat"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ('id', 'reviewer_info', 'provider_info', 'star_display', 'short_comment', 'created_at')
    list_filter     = ('rating', 'created_at')
    search_fields   = ('reviewer__username', 'provider__username', 'comment')
    readonly_fields = ('reviewer', 'provider', 'service_request', 'created_at')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    list_per_page   = 25

    def reviewer_info(self, obj):
        return format_html('<b>{}</b>', obj.reviewer.username)
    reviewer_info.short_description = "Mijoz"

    def provider_info(self, obj):
        return format_html('<b>🛠️ {}</b>', obj.provider.username)
    provider_info.short_description = "Usta"

    def star_display(self, obj):
        filled = '⭐' * obj.rating
        return format_html('<span style="font-size:14px" title="{}/5">{} (<b>{}</b>)</span>', obj.rating, filled, obj.rating)
    star_display.short_description = "Reyting"

    def short_comment(self, obj):
        if not obj.comment:
            return format_html('<span style="color:#9ca3af">—</span>')
        return obj.comment[:70] + ('...' if len(obj.comment) > 70 else '')
    short_comment.short_description = "Izoh"

