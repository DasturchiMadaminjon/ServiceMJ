import logging

from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models as db_models

from accounts.permissions import IsClient, IsProvider
from .models import Category, Skill, ProviderProfile, PortfolioItem
from .serializers import (
    CategorySerializer, SkillSerializer, ProviderProfileSerializer,
    PortfolioItemSerializer
)
from orders.models import Review
from orders.serializers import ReviewSerializer

logger = logging.getLogger(__name__)


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
            try:
                category_ids = [int(category_id)]
                
                def get_all_descendants(cat_id):
                    sub_ids = list(Category.objects.filter(parent_id=cat_id).values_list('id', flat=True))
                    descendants = []
                    for s_id in sub_ids:
                        descendants.append(s_id)
                        descendants.extend(get_all_descendants(s_id))
                    return descendants

                category_ids.extend(get_all_descendants(int(category_id)))
                qs = qs.filter(skills__category_id__in=category_ids).distinct()
            except ValueError:
                pass
        return qs

    def get_authenticators(self):
        if self.request.method == 'GET' and self.kwargs.get('pk') != 'me':
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'reviews'):
            if self.kwargs.get('pk') == 'me':
                return [permissions.IsAuthenticated()]
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsProvider()]

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            if not self.request.user.is_authenticated:
                from rest_framework.exceptions import NotAuthenticated
                raise NotAuthenticated()
            return get_object_or_404(ProviderProfile, user=self.request.user)
        return super().get_object()

    def perform_create(self, serializer):
        if ProviderProfile.objects.filter(user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Siz allaqachon profil yaratgansiz.")
        # save() metodi avtomatik user.role = 'provider' qiladi
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

    def get_authenticators(self):
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

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
        # get_or_create: agar profil bo'lmasa, avtomatik yaratiladi
        # Bu eski foydalanuvchilar uchun ham ishlaydi
        profile, created = ProviderProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'bio': '', 'experience_years': 0}
        )
        if created:
            logger.info(
                "[PORTFOLIO] ProviderProfile avtomatik yaratildi | user=%s",
                self.request.user.username
            )
        serializer.save(provider=profile)




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
        from orders.models import ServiceRequest, Review
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
