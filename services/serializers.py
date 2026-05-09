from rest_framework import serializers
from .models import Category, ProviderProfile, ServiceRequest

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProviderProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = ProviderProfile
        fields = ('id', 'username', 'bio', 'experience_years', 'rating')

class ServiceRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = ('id', 'customer_name', 'category', 'category_name', 'description', 'status', 'created_at')
        read_only_fields = ('status', 'customer')
