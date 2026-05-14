from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, ServiceRequest, ProviderProfile, Skill

User = get_user_model()

class ServiceHubTDDTest(APITestCase):
    def setUp(self):
        # Foydalanuvchilarni yaratish
        self.client_user = User.objects.create_user(username='client1', password='password123', role='client')
        self.provider_user = User.objects.create_user(username='provider1', password='password123', role='provider')
        
        # Provider profile yaratish
        self.provider_profile = ProviderProfile.objects.create(user=self.provider_user, bio="Usta bio")
        
        # Kategoriya yaratish
        self.category = Category.objects.create(name="Santexnika")

    def test_client_can_create_request(self):
        """Mijoz buyurtma yarata olishi kerak."""
        self.client.force_authenticate(user=self.client_user)
        data = {
            "category": self.category.id,
            "description": "Kran buzuldi"
        }
        response = self.client.post('/api/services/requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceRequest.objects.count(), 1)
        print("SUCCESS: Mijoz buyurtma yaratish testi o'tdi!")

    def test_provider_cannot_create_request(self):
        """Usta buyurtma yarata olmasligi kerak (Business Logic Error fix)."""
        self.client.force_authenticate(user=self.provider_user)
        data = {
            "category": self.category.id,
            "description": "Men ham buyurtma bermoqchiman"
        }
        response = self.client.post('/api/services/requests/', data)
        # Bizda IsClient ruxsati bor, shuning uchun 403 bo'lishi kerak
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("SUCCESS: Usta buyurtma bera olmaslik (Permission) testi o'tdi!")

    def test_provider_can_accept_request(self):
        """Usta kutilayotgan buyurtmani qabul qila olishi kerak."""
        req = ServiceRequest.objects.create(customer=self.client_user, category=self.category, description="Test")
        
        self.client.force_authenticate(user=self.provider_user)
        response = self.client.post(f'/api/services/requests/{req.id}/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'accepted')
        self.assertEqual(req.provider, self.provider_profile)
        print("SUCCESS: Usta buyurtmani qabul qilish testi o'tdi!")

    def test_review_only_on_completed_request(self):
        """Faqat tugatilgan buyurtmalarga sharh qoldirish mumkinligini tekshirish."""
        req = ServiceRequest.objects.create(
            customer=self.client_user, 
            provider=self.provider_profile,
            category=self.category, 
            status='accepted' # Hali tugamagan
        )
        
        self.client.force_authenticate(user=self.client_user)
        data = {
            "request": req.id,
            "rating": 5,
            "comment": "Yaxshi!"
        }
        response = self.client.post('/api/services/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Endi tugatamiz
        req.status = 'completed'
        req.save()
        
        response = self.client.post('/api/services/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print("SUCCESS: Sharh qoldirish (Validation) testi o'tdi!")
