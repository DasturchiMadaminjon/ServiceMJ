from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Skill, ProviderProfile, PortfolioItem, ServiceRequest, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'icon', 'skill_count')
    search_fields = ('name',)
    list_filter = ('parent',)

    def skill_count(self, obj):
        return obj.skills.count()
    skill_count.short_description = "Ko'nikmalar soni"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'experience_years', 'is_active', 'hourly_rate')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'bio')
    readonly_fields = ('rating',)
    filter_horizontal = ('skills',)


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'created_at')
    search_fields = ('title', 'provider__user__username')


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
