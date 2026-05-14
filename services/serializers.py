from rest_framework import serializers
from .models import Category, ProviderProfile, ServiceRequest, Skill, Portfolio, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'
        read_only_fields = ('provider',)

class ProviderProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    portfolio_items = PortfolioSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProviderProfile
        fields = ('id', 'username', 'bio', 'experience_years', 'rating', 'skills', 'portfolio_items')

class ServiceRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.user.username', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = ('id', 'customer_name', 'category', 'category_name', 'description', 'status', 'provider', 'provider_name', 'created_at')
        read_only_fields = ('status', 'customer', 'provider')

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('customer', 'provider')

    def validate(self, attrs):
        request = attrs.get('request')
        if request.status != 'completed':
            raise serializers.ValidationError("Faqat yakunlangan buyurtmalarga sharh qoldirish mumkin.")
        return attrs
