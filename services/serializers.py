from rest_framework import serializers
from .models import Category, Skill, ProviderProfile, PortfolioItem
from accounts.serializers import UserSerializer


class SkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')

    class Meta:
        model = Skill
        fields = ('id', 'name', 'category', 'category_name')


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    skill_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'icon', 'children', 'skill_count')

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

    def get_skill_count(self, obj):
        return obj.skills.count()


class PortfolioItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioItem
        fields = ('id', 'title', 'description', 'image', 'image_url', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class ProviderProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), many=True, write_only=True,
        source='skills', required=False
    )
    portfolio_items = PortfolioItemSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = ProviderProfile
        fields = (
            'id', 'user', 'bio', 'experience_years', 'rating',
            'is_active', 'skills', 'skill_ids', 'hourly_rate',
            'portfolio_items', 'review_count'
        )
        read_only_fields = ('id', 'rating', 'user')

    def get_review_count(self, obj):
        return obj.user.received_reviews.count()
