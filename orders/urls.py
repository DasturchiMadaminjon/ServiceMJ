from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceRequestViewSet, ReviewViewSet, MyServiceRequestsView

router = DefaultRouter()
router.register(r'requests', ServiceRequestViewSet, basename='service-request')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('my-requests/', MyServiceRequestsView.as_view(), name='my-requests'),
]
