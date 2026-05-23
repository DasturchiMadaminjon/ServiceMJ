from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Skill, ProviderProfile, PortfolioItem


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



