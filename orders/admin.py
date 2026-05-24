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
    list_display         = ('id', 'customer', 'category', 'status_badge', 'status', 'provider', 'budget', 'currency', 'created_at')
    list_filter          = ('status', 'category', 'currency')
    search_fields        = ('customer__username', 'description', 'address')
    readonly_fields      = ('created_at', 'updated_at')
    list_editable        = ('status',)
    list_per_page        = 25
    date_hierarchy       = 'created_at'
    ordering             = ('-created_at',)
    actions = [
        cancel_requests,
        complete_requests,
        reset_to_pending,
        mark_in_progress,
        # Django built-in: 'delete_selected' ham avtomatik mavjud
    ]

    def get_list_display_links(self, request, list_display):
        return ('id',)

    def status_badge(self, obj):
        """Status uchun rangli badge ko'rinishi."""
        colors = {
            'pending':     ('#f59e0b', 'Kutilmoqda'),
            'accepted':    ('#3b82f6', 'Qabul qilindi'),
            'in_progress': ('#8b5cf6', 'Jarayonda'),
            'completed':   ('#10b981', 'Tugallandi'),
            'cancelled':   ('#ef4444', 'Bekor qilindi'),
        }
        color, label = colors.get(obj.status, ('#6b7280', obj.status))
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:12px;font-size:12px;font-weight:600">{}</span>',
            color, label
        )
    status_badge.short_description = "Holat"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ('id', 'reviewer', 'provider', 'star_display', 'short_comment', 'created_at')
    list_filter     = ('rating', 'created_at')
    search_fields   = ('reviewer__username', 'provider__username', 'comment')
    readonly_fields = ('reviewer', 'provider', 'service_request', 'created_at')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    list_per_page   = 25
    # Django built-in 'delete_selected' avtomatik mavjud

    def star_display(self, obj):
        filled   = '⭐' * obj.rating
        empty    = '☆' * (5 - obj.rating)
        return format_html(
            '<span title="{}/5">{}{}</span>',
            obj.rating, filled, empty
        )
    star_display.short_description = "Reyting"

    def short_comment(self, obj):
        if not obj.comment:
            return format_html('<span style="color:gray">—</span>')
        return obj.comment[:60] + ('...' if len(obj.comment) > 60 else '')
    short_comment.short_description = "Izoh"
