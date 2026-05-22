from rest_framework import serializers
from django.conf import settings
from .models import CustomUser

# 10 MB = 10 * 1024 * 1024 bayt
MAX_AVATAR_SIZE = 10 * 1024 * 1024


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = CustomUser
        fields = ('username', 'password', 'phone_number', 'role', 'email')
        extra_kwargs = {'email': {'required': False}}

    def validate_role(self, value):
        if value not in ('client', 'provider'):
            raise serializers.ValidationError(
                "Rol faqat 'client' yoki 'provider' bo'lishi mumkin."
            )
        return value

    def validate_phone_number(self, value):
        if not value or value.strip() == '':
            return None
        return value

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            role=validated_data.get('role', 'client'),
            email=validated_data.get('email', ''),
        )


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model  = CustomUser
        fields = (
            'id', 'username', 'email', 'role',
            'phone_number', 'is_verified', 'avatar', 'avatar_url', 'password'
        )
        read_only_fields = ('id', 'username', 'is_verified')
        extra_kwargs = {'avatar': {'write_only': True, 'required': False}}

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url

    def validate_avatar(self, value):
        if value and value.size > MAX_AVATAR_SIZE:
            mb = value.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"Rasm hajmi {mb:.1f} MB. Maksimal ruxsat etilgan hajm: 10 MB."
            )
        return value

    def validate_phone_number(self, value):
        if not value or value.strip() == '':
            return None
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
