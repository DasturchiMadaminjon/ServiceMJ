from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.cache import cache

User = get_user_model()

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', 
            phone_number='+998990000000',
            password='testpassword123'
        )

    def test_login_with_phone(self):
        """Telefon raqami orqali login qilishni tekshirish"""
        response = self.client.post('/api/accounts/token/', {
            'username': '+998990000000',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_otp_generation(self):
        """OTP kod yaratilishini tekshirish"""
        # Login (token olish)
        response = self.client.post('/api/accounts/token/', {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        
        # OTP yuborish
        otp_resp = self.client.post('/api/accounts/send-otp/')
        self.assertEqual(otp_resp.status_code, 200)
        self.assertTrue(otp_resp.data['status'] == 'ok')
        
        # Redis'da kod saqlanganini tekshirish
        cache_key = f"otp_{self.user.id}"
        self.assertIsNotNone(cache.get(cache_key))
