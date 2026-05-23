from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models as db_models
from django.shortcuts import get_object_or_404

from accounts.permissions import IsClient, IsProvider
from .models import ServiceRequest, Review
from .serializers import (
    ServiceRequestSerializer, StatusUpdateSerializer, ReviewSerializer
)
from .logic import update_request_status
from django.core.exceptions import ValidationError, PermissionDenied


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
        if getattr(self, 'swagger_fake_view', False):
            return ServiceRequest.objects.none()
        
        user = self.request.user
        
        if user.is_staff:
            qs = ServiceRequest.objects.all()
        elif getattr(user, 'role', None) == 'client':
            qs = ServiceRequest.objects.filter(customer=user)
        elif getattr(user, 'role', None) == 'provider':
            qs = ServiceRequest.objects.filter(
                db_models.Q(provider=user) | db_models.Q(status='pending')
            )
        else:
            return ServiceRequest.objects.none()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.select_related('customer', 'provider', 'category')

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
        """
        Status o'zgartirish API-si. Asosiy mantiq (transaction va lock) logic.py da joylashgan.
        Bu "Millionlab foydalanuvchilar orasida Race Condition" oldini oladi.
        """
        serializer = StatusUpdateSerializer(data=request.data, context={'instance': self.get_object()})
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        try:
            # logic.py ga murojaat (tranzaksiya shu yerda boshqariladi)
            updated_instance = update_request_status(pk, request.user, new_status)
            return Response(ServiceRequestSerializer(updated_instance, context={'request': request}).data)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "Tizim xatosi yuz berdi.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_authenticators(self):
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

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
