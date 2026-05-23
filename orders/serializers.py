from rest_framework import serializers
from .models import ServiceRequest, Review
from accounts.serializers import UserSerializer

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
            'budget', 'currency', 'created_at', 'updated_at', 'can_review'
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
