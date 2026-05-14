from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProviderProfileViewSet, ServiceRequestViewSet,
    SkillViewSet, PortfolioViewSet, ReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'portfolio', PortfolioViewSet)
router.register(r'providers', ProviderProfileViewSet)
router.register(r'requests', ServiceRequestViewSet, basename='servicerequest')
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
