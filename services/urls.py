from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SkillViewSet, ProviderProfileViewSet,
    PortfolioItemViewSet, ServiceRequestViewSet, ReviewViewSet,
    MyServiceRequestsView, DashboardStatsView,
)

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('skills', SkillViewSet, basename='skill')
router.register('providers', ProviderProfileViewSet, basename='providerprofile')
router.register('requests', ServiceRequestViewSet, basename='servicerequest')
router.register('reviews', ReviewViewSet, basename='review')

# Provider portfolio: /api/services/providers/{pk}/portfolio/
provider_portfolio = PortfolioItemViewSet.as_view({
    'get': 'list', 'post': 'create'
})
provider_portfolio_detail = PortfolioItemViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})

urlpatterns = [
    path('', include(router.urls)),
    path(
        'providers/<int:provider_pk>/portfolio/',
        provider_portfolio, name='provider-portfolio-list'
    ),
    path(
        'providers/<int:provider_pk>/portfolio/<int:pk>/',
        provider_portfolio_detail, name='provider-portfolio-detail'
    ),
    path('my-requests/', MyServiceRequestsView.as_view(), name='my-requests'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
