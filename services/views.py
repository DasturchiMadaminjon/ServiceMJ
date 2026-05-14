from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Category, ProviderProfile, ServiceRequest, Skill, Portfolio, Review
from .serializers import (
    CategorySerializer, ProviderProfileSerializer, ServiceRequestSerializer,
    SkillSerializer, PortfolioSerializer, ReviewSerializer
)
from .permissions import IsClient, IsProvider, IsOwnerOrReadOnly

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAdminUser]

class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsProvider, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider_profile)

class ProviderProfileViewSet(viewsets.ModelViewSet):
    queryset = ProviderProfile.objects.filter(is_active=True)
    serializer_class = ProviderProfileSerializer
    permission_classes = [IsOwnerOrReadOnly]

class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsClient()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return ServiceRequest.objects.filter(customer=user)
        elif user.role == 'provider':
            return ServiceRequest.objects.filter(models.Q(provider=user.provider_profile) | models.Q(status='pending'))
        return ServiceRequest.objects.all()

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsProvider])
    def accept(self, request, pk=None):
        service_request = self.get_object()
        if service_request.status != 'pending':
            return Response({'error': 'Faqat kutilayotgan buyurtmalarni qabul qilish mumkin.'}, status=status.HTTP_400_BAD_REQUEST)
        
        service_request.status = 'accepted'
        service_request.provider = request.user.provider_profile
        service_request.save()
        return Response({'status': 'Buyurtma qabul qilindi'})

    @action(detail=True, methods=['post'], permission_classes=[IsProvider])
    def complete(self, request, pk=None):
        service_request = self.get_object()
        if service_request.provider != request.user.provider_profile:
            return Response({'error': 'Siz ushbu buyurtma ustasi emassiz.'}, status=status.HTTP_403_FORBIDDEN)
        
        service_request.status = 'completed'
        service_request.save()
        return Response({'status': 'Buyurtma yakunlandi'})

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsClient()]
        return [IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        request = serializer.validated_data['request']
        serializer.save(
            customer=self.request.user,
            provider=request.provider
        )
