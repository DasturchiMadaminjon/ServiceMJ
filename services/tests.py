from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomUser
from .models import Category, ServiceRequest

class ServicesTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='tester', password='testpassword', role='client')
        self.category = Category.objects.create(name='Santexnika')
        self.client.force_authenticate(user=self.user)

    def test_category_list(self):
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_request(self):
        url = reverse('servicerequest-list')
        data = {
            'category': self.category.id,
            'description': 'Kran buzildi, yordam kerak.'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceRequest.objects.count(), 1)
        self.assertEqual(ServiceRequest.objects.get().customer, self.user)

    def test_unauthenticated_access(self):
        self.client.logout()
        url = reverse('servicerequest-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
