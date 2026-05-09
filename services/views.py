from rest_framework import viewsets, permissions
from .models import Category, ProviderProfile, ServiceRequest
from .serializers import CategorySerializer, ProviderProfileSerializer, ServiceRequestSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class ProviderProfileViewSet(viewsets.ModelViewSet):
    queryset = ProviderProfile.objects.filter(is_active=True)
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return ServiceRequest.objects.filter(customer=user)
        return ServiceRequest.objects.all()

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
