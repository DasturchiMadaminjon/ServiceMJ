from rest_framework import serializers
from .models import Category, Skill, ProviderProfile, PortfolioItem, ServiceRequest, Review
from accounts.serializers import UserSerializer


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'category')


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


class ServiceRequestSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    provider_info = UserSerializer(source='provider', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    can_review = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'customer', 'provider', 'provider_info', 'category',
            'category_name', 'description', 'status', 'address',
            'budget', 'created_at', 'updated_at', 'can_review'
        )
        read_only_fields = ('id', 'customer', 'status', 'created_at', 'updated_at')

    def get_can_review(self, obj):
        return obj.status == 'completed' and not hasattr(obj, 'review')


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ServiceRequest.STATUS_CHOICES)

    def validate(self, attrs):
        instance = self.context.get('instance')
        new_status = attrs['status']
        if instance and not instance.can_transition_to(new_status):
            raise serializers.ValidationError(
                f"'{instance.status}' holatidan '{new_status}' holatiga o'tish mumkin emas."
            )
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    provider_name = serializers.CharField(source='provider.username', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'service_request', 'reviewer', 'reviewer_name',
            'provider', 'provider_name', 'rating', 'comment', 'created_at'
        )
        read_only_fields = ('id', 'reviewer', 'provider', 'created_at')

    def validate_service_request(self, value):
        request = self.context.get('request')
        if value.status != 'completed':
            raise serializers.ValidationError("Faqat tugallangan so'rovlarga sharh yozish mumkin.")
        if value.customer != request.user:
            raise serializers.ValidationError("Faqat so'rov bergan mijoz sharh yoza oladi.")
        if hasattr(value, 'review'):
            raise serializers.ValidationError("Bu so'rovga sharh allaqachon yozilgan.")
        if not value.provider:
            raise serializers.ValidationError("Bu so'rovda usta belgilanmagan.")
        return value

    def create(self, validated_data):
        service_request = validated_data['service_request']
        validated_data['reviewer'] = self.context['request'].user
        validated_data['provider'] = service_request.provider
        return super().create(validated_data)
