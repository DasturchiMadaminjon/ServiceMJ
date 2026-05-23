from django.contrib import admin
from .models import ServiceRequest, Review

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'category', 'status', 'provider', 'budget', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('customer__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

    def get_list_display_links(self, request, list_display):
        return ('id',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'provider', 'rating', 'stars', 'created_at')
    list_filter = ('rating',)
    search_fields = ('reviewer__username', 'provider__username', 'comment')
    readonly_fields = ('reviewer', 'provider', 'service_request', 'created_at')

    def stars(self, obj):
        return '⭐' * obj.rating
    stars.short_description = "Reyting"
