from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models as db_models

from accounts.permissions import IsClient, IsProvider
from .models import Category, Skill, ProviderProfile, PortfolioItem, ServiceRequest, Review
from .serializers import (
    CategorySerializer, SkillSerializer, ProviderProfileSerializer,
    PortfolioItemSerializer, ServiceRequestSerializer,
    StatusUpdateSerializer, ReviewSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(parent=None).prefetch_related('children', 'skills').order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.select_related('category').all().order_by('id')
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProviderProfileViewSet(viewsets.ModelViewSet):
    queryset = ProviderProfile.objects.filter(is_active=True).select_related('user').prefetch_related('skills')
    serializer_class = ProviderProfileSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'bio', 'skills__name']
    ordering_fields = ['rating', 'experience_years']
    ordering = ['-rating']

    def get_queryset(self):
        # Swagger uchun guard
        if getattr(self, 'swagger_fake_view', False):
            return ProviderProfile.objects.none()
            
        qs = ProviderProfile.objects.filter(is_active=True).select_related('user').prefetch_related('skills')
        category_id = self.request.query_params.get('skills__category')
        if category_id:
            qs = qs.filter(skills__category_id=category_id).distinct()
        return qs

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'reviews'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsProvider()]

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return get_object_or_404(ProviderProfile, user=self.request.user)
        return super().get_object()

    def perform_create(self, serializer):
        if ProviderProfile.objects.filter(user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Siz allaqachon profil yaratgansiz.")
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def reviews(self, request, pk=None):
        profile = self.get_object()
        reviews = Review.objects.filter(provider=profile.user).select_related('reviewer')
        page = self.paginate_queryset(reviews)
        serializer = ReviewSerializer(page or reviews, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class PortfolioItemViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioItemSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsProvider()]

    def get_queryset(self):
        # Swagger schema generation guard
        if getattr(self, 'swagger_fake_view', False):
            return PortfolioItem.objects.none()
        provider_pk = self.kwargs.get('provider_pk')
        if provider_pk:
            return PortfolioItem.objects.filter(provider_id=provider_pk)
        if self.request.user.is_authenticated:
            return PortfolioItem.objects.filter(provider__user=self.request.user)
        return PortfolioItem.objects.none()

    def perform_create(self, serializer):
        profile = get_object_or_404(ProviderProfile, user=self.request.user)
        serializer.save(provider=profile)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'category__name']
    ordering_fields = ['created_at', 'budget']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsClient()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Swagger schema generation guard
        if getattr(self, 'swagger_fake_view', False):
            return ServiceRequest.objects.none()
        user = self.request.user
        if user.is_staff:
            return ServiceRequest.objects.all().select_related('customer', 'provider', 'category')
        if getattr(user, 'role', None) == 'client':
            return ServiceRequest.objects.filter(customer=user).select_related('customer', 'provider', 'category')
        if getattr(user, 'role', None) == 'provider':
            return ServiceRequest.objects.filter(
                db_models.Q(provider=user) | db_models.Q(status='pending')
            ).select_related('customer', 'provider', 'category')
        return ServiceRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.customer != request.user and not request.user.is_staff:
            return Response(
                {"detail": "Faqat buyurtma egasi tahrirlashi mumkin."},
                status=status.HTTP_403_FORBIDDEN
            )
        if instance.status not in ('pending',):
            return Response(
                {"detail": "Faqat 'pending' holatidagi so'rovni tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        instance = self.get_object()
        # Eski statusni saqlash (signal uchun)
        instance._old_status = instance.status

        serializer = StatusUpdateSerializer(
            data=request.data, context={'instance': instance, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        user = request.user
        if new_status == 'accepted':
            if not hasattr(user, 'role') or user.role != 'provider':
                return Response(
                    {"detail": "Faqat usta qabul qila oladi."},
                    status=status.HTTP_403_FORBIDDEN
                )
            instance.provider = user

        elif new_status in ('in_progress', 'completed'):
            if instance.provider != user and not user.is_staff:
                return Response(
                    {"detail": "Faqat tayinlangan usta holat o'zgartira oladi."},
                    status=status.HTTP_403_FORBIDDEN
                )

        elif new_status == 'cancelled':
            if instance.customer != user and instance.provider != user and not user.is_staff:
                return Response(
                    {"detail": "Bekor qilish uchun ruxsat yo'q."},
                    status=status.HTTP_403_FORBIDDEN
                )

        instance.status = new_status
        instance.save()
        return Response(ServiceRequestSerializer(instance, context={'request': request}).data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsClient()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Review.objects.select_related('reviewer', 'provider', 'service_request').all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.reviewer != request.user and not request.user.is_staff:
            return Response(
                {"detail": "Faqat sharh egasi o'chira oladi."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class MyServiceRequestsView(generics.ListAPIView):
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status')
        qs = ServiceRequest.objects.filter(customer=user).select_related('category', 'provider')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class DashboardStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = None

    def get_serializer_class(self):
        from rest_framework import serializers
        class DashboardSerializer(serializers.Serializer):
            pass
        return DashboardSerializer

    def get(self, request):
        from accounts.models import CustomUser
        stats = {
            'total_users': CustomUser.objects.count(),
            'total_clients': CustomUser.objects.filter(role='client').count(),
            'total_providers': CustomUser.objects.filter(role='provider').count(),
            'total_requests': ServiceRequest.objects.count(),
            'requests_by_status': dict(
                ServiceRequest.objects.values('status')
                .annotate(count=db_models.Count('id'))
                .values_list('status', 'count')
            ),
            'total_reviews': Review.objects.count(),
            'avg_rating': float(Review.objects.aggregate(
                avg=db_models.Avg('rating')
            )['avg'] or 0),
        }
        return Response(stats)
