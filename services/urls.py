from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProviderProfileViewSet, ServiceRequestViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'providers', ProviderProfileViewSet)
router.register(r'requests', ServiceRequestViewSet, basename='servicerequest')

urlpatterns = [
    path('', include(router.urls)),
]
