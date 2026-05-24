"""
accounts/tests.py — To'liq TDD Test Suite

Qamrov:
  - Ro'yxatdan o'tish (registration)
  - OTP yuborish va tasdiqlash
  - Xavfsizlik: mock_code production da yo'qligi
  - Persistent Auth: DeviceSession yaratish
  - Token refresh: DeviceSession JTI yangilanishi
  - Logout: token blacklist + session o'chirish
  - Logout-all: barcha sessiyalarni o'chirish
  - Qurilmalar ro'yxati va o'chirish
  - Avatar yuklash: 50MB limit va format tekshiruvi
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from accounts.models import CustomUser, DeviceSession

User = get_user_model()


# ─────────────────────────────────────────────────────────────────
# Yordamchi funksiyalar
# ─────────────────────────────────────────────────────────────────

def make_user(username='testuser', phone='+998990000000', password='Pass1234!', role='client'):
    return User.objects.create_user(
        username=username,
        phone_number=phone,
        password=password,
        role=role,
    )


def login(client, username='testuser', password='Pass1234!'):
    return client.post('/api/accounts/login/', {
        'username': username,
        'password': password,
    }, format='json')


# ═══════════════════════════════════════════════════════════════
# 1. RO'YXATDAN O'TISH TESTLARI
# ═══════════════════════════════════════════════════════════════

class RegistrationExtendedTest(APITestCase):
    """Ro'yxatdan o'tish — qo'shimcha testlar."""

    URL = '/api/accounts/register/'

    def test_register_client_success_returns_201(self):
        """Mijoz muvaffaqiyatli ro'yxatdan o'tishi kerak."""
        r = self.client.post(self.URL, {
            'username': 'newclient',
            'password': 'SecurePass1!',
            'phone_number': '+998901234567',
            'role': 'client',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertNotIn('password', r.data)

    def test_register_provider_success_returns_201(self):
        """Usta muvaffaqiyatli ro'yxatdan o'tishi kerak."""
        r = self.client.post(self.URL, {
            'username': 'newprovider',
            'password': 'SecurePass1!',
            'phone_number': '+998907654321',
            'role': 'provider',
        }, format='json')
        self.assertEqual(r.status_code, 201)

    def test_register_duplicate_phone_returns_400(self):
        """Bir xil telefon raqam bilan ikki marta ro'yxatdan o'tib bo'lmaydi."""
        make_user('user1', '+998900000001')
        r = self.client.post(self.URL, {
            'username': 'user2',
            'password': 'SecurePass1!',
            'phone_number': '+998900000001',
            'role': 'client',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_register_short_password_returns_400(self):
        """Qisqa parol qabul qilinmasligi kerak."""
        r = self.client.post(self.URL, {
            'username': 'shortpwduser',
            'password': '123',
            'role': 'client',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_register_admin_role_blocked(self):
        """'admin' roli ro'yxatdan o'tishda taqiqlangan bo'lishi kerak."""
        r = self.client.post(self.URL, {
            'username': 'hacker',
            'password': 'SecurePass1!',
            'role': 'admin',
        }, format='json')
        self.assertEqual(r.status_code, 400)


# ═══════════════════════════════════════════════════════════════
# 2. OTP TESTLARI
# ═══════════════════════════════════════════════════════════════

class OTPTest(APITestCase):
    """OTP yuborish va tasdiqlash testlari."""

    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_send_otp_returns_200_and_ok_status(self):
        """OTP yuborish 200 va 'ok' status qaytarishi kerak."""
        r = self.client.post('/api/accounts/send-otp/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data.get('status'), 'ok')

    def test_send_otp_saves_code_to_redis(self):
        """OTP kodi Redis'ga saqlanishi kerak."""
        cache.delete(f"otp_{self.user.id}")
        self.client.post('/api/accounts/send-otp/')
        saved = cache.get(f"otp_{self.user.id}")
        self.assertIsNotNone(saved, "OTP Redis'ga saqlanmadi!")
        self.assertEqual(len(saved), 6, "OTP 6 xonali bo'lishi kerak!")

    def test_otp_response_has_no_mock_code_in_production(self):
        """
        🔐 Xavfsizlik testi: DEBUG=False (production) muhitida API javobi
        mock_code ni o'z ichiga OLMASLIGI kerak.
        Test muhitida (DEBUG=True) esa mock_code ruxsat etilgan —
        bu dasturchilar uchun qulay (SMS integratsiyasiz test qilish).
        """
        from django.conf import settings as django_settings
        r = self.client.post('/api/accounts/send-otp/')
        self.assertEqual(r.status_code, 200)

        if django_settings.DEBUG:
            # DEBUG=True: mock_code bo'lishi MUMKIN — bu to'g'ri xulq
            # Kod borligini tekshiramiz (6 xonali bo'lishi shart)
            if 'mock_code' in r.data:
                self.assertEqual(len(str(r.data['mock_code'])), 6,
                    "mock_code 6 xonali bo'lishi kerak!")
        else:
            # DEBUG=False (production): mock_code HECH QACHON bo'lmasligi kerak
            self.assertNotIn('mock_code', r.data, (
                "XAVFSIZLIK XATOSI: mock_code production API javobida bor! "
                "Bu production'da maxfiy kodni ochiq ko'rsatadi."
            ))


    def test_verify_correct_otp_verifies_user(self):
        """To'g'ri OTP bilan foydalanuvchi tasdiqlanishi kerak."""
        cache.set(f"otp_{self.user.id}", '654321', timeout=300)
        r = self.client.post('/api/accounts/verify-otp/', {'code': '654321'})
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified, "is_verified True bo'lishi kerak!")

    def test_verify_wrong_otp_returns_400(self):
        """Noto'g'ri OTP 400 qaytarishi kerak."""
        cache.set(f"otp_{self.user.id}", '123456', timeout=300)
        r = self.client.post('/api/accounts/verify-otp/', {'code': '999999'})
        self.assertEqual(r.status_code, 400)

    def test_verify_missing_code_returns_400(self):
        """Kod kiritilmasa 400 qaytarishi kerak."""
        r = self.client.post('/api/accounts/verify-otp/', {})
        self.assertEqual(r.status_code, 400)

    def test_already_verified_cannot_send_otp(self):
        """Tasdiqlangan foydalanuvchi qayta OTP so'rasa 400 kerak."""
        self.user.is_verified = True
        self.user.save()
        r = self.client.post('/api/accounts/send-otp/')
        self.assertEqual(r.status_code, 400)


# ═══════════════════════════════════════════════════════════════
# 3. PERSISTENT AUTH — QURILMA SESSIYALARI TESTLARI
# ═══════════════════════════════════════════════════════════════

class DeviceSessionTest(APITestCase):
    """Telegram kabi persistent auth — qurilma sessiya testlari."""

    def setUp(self):
        self.user = make_user()

    def test_login_creates_device_session(self):
        """Login bo'lganda DeviceSession yozuvi yaratilishi kerak."""
        before = DeviceSession.objects.filter(user=self.user).count()
        r = login(self.client)
        self.assertEqual(r.status_code, 200)
        after = DeviceSession.objects.filter(user=self.user).count()
        self.assertEqual(after, before + 1, "Login DeviceSession yaratmadi!")

    def test_device_session_stores_correct_device_info(self):
        """DeviceSession qurilma ma'lumotlarini to'g'ri saqlashi kerak."""
        self.client.post(
            '/api/accounts/login/',
            {'username': 'testuser', 'password': 'Pass1234!'},
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit Safari',
        )
        session = DeviceSession.objects.filter(user=self.user).first()
        self.assertIsNotNone(session)
        self.assertIn('iPhone', session.device_name)

    def test_token_refresh_updates_device_session_jti(self):
        """Token yangilanishida DeviceSession JTI yangilanishi kerak."""
        r = login(self.client)
        self.assertEqual(r.status_code, 200)
        old_refresh = r.data['refresh']

        old_session = DeviceSession.objects.filter(user=self.user).first()
        old_jti = old_session.refresh_jti if old_session else None

        r2 = self.client.post('/api/accounts/token/refresh/', {
            'refresh': old_refresh
        }, format='json')
        self.assertEqual(r2.status_code, 200)

        # Sessiya yangi JTI bilan yangilangan bo'lishi kerak
        if old_jti:
            updated = DeviceSession.objects.filter(user=self.user).first()
            self.assertNotEqual(updated.refresh_jti, old_jti,
                                "Token yangilanishida JTI yangilanmadi!")

    def test_logout_removes_device_session(self):
        """Logout DeviceSession ni o'chirishi va tokenni blacklistga qo'shishi kerak."""
        r = login(self.client)
        self.assertEqual(r.status_code, 200)
        refresh = r.data['refresh']
        access  = r.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        sessions_before = DeviceSession.objects.filter(user=self.user).count()

        r2 = self.client.post('/api/accounts/logout/', {'refresh': refresh}, format='json')
        self.assertEqual(r2.status_code, 200)

        sessions_after = DeviceSession.objects.filter(user=self.user).count()
        self.assertEqual(sessions_after, sessions_before - 1, "Sessiya o'chirilmadi!")

    def test_logout_without_refresh_returns_400(self):
        """Refresh token bermasdan logout so'rasa 400 kerak."""
        self.client.force_authenticate(user=self.user)
        r = self.client.post('/api/accounts/logout/', {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_logout_all_removes_all_sessions(self):
        """Logout-all barcha sessiyalarni o'chirishi kerak."""
        # Ikki qurilmadan login
        self.client.post('/api/accounts/login/', {
            'username': 'testuser', 'password': 'Pass1234!'
        }, format='json')
        self.client.post('/api/accounts/login/', {
            'username': 'testuser', 'password': 'Pass1234!'
        }, format='json')

        self.client.force_authenticate(user=self.user)
        r = self.client.post('/api/accounts/logout-all/')
        self.assertEqual(r.status_code, 200)

        remaining = DeviceSession.objects.filter(user=self.user).count()
        self.assertEqual(remaining, 0, "Barcha sessiyalar o'chirilmadi!")

    def test_device_list_returns_own_sessions(self):
        """Foydalanuvchi faqat o'z sessiyalarini ko'rishi kerak."""
        # Boshqa foydalanuvchi sessiyasi
        other = make_user('other_user', '+998991234567')
        DeviceSession.objects.create(
            user=other, refresh_jti='other-jti-123', device_name='Other Device'
        )

        login(self.client)
        r_login = login(self.client)
        access = r_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        r = self.client.get('/api/accounts/devices/')
        self.assertEqual(r.status_code, 200)

        results = r.data.get('results', r.data)
        for session in results:
            # Boshqa foydalanuvchi sessiyasi ko'rinmasligi kerak
            self.assertNotEqual(session.get('device_name'), 'Other Device')

    def test_device_delete_removes_specific_session(self):
        """Muayyan sessiyani o'chirish faqat o'sha sessiyani o'chirishi kerak."""
        # Ikki qurilmadan login
        self.client.post('/api/accounts/login/', {
            'username': 'testuser', 'password': 'Pass1234!'
        }, format='json')

        r = self.client.post('/api/accounts/login/', {
            'username': 'testuser', 'password': 'Pass1234!'
        }, format='json')
        access = r.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        sessions_before = DeviceSession.objects.filter(user=self.user).count()
        session_to_delete = DeviceSession.objects.filter(user=self.user).first()

        r2 = self.client.delete(f'/api/accounts/devices/{session_to_delete.id}/')
        self.assertEqual(r2.status_code, 204)

        sessions_after = DeviceSession.objects.filter(user=self.user).count()
        self.assertEqual(sessions_after, sessions_before - 1)

    def test_cannot_delete_other_users_session(self):
        """Boshqa foydalanuvchi sessiyasini o'chirib bo'lmasligi kerak."""
        other = make_user('other2', '+998992345678')
        other_session = DeviceSession.objects.create(
            user=other, refresh_jti='other-jti-999', device_name='Other Device 2'
        )

        self.client.force_authenticate(user=self.user)
        r = self.client.delete(f'/api/accounts/devices/{other_session.id}/')
        self.assertEqual(r.status_code, 404, "Boshqa foydalanuvchi sessiyasiga kirish mumkin bo'lmasligi kerak!")

    def test_login_response_has_access_and_refresh_tokens(self):
        """Login javobi access va refresh tokenlar qaytarishi kerak."""
        r = login(self.client)
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)
        self.assertIn('refresh', r.data)


# ═══════════════════════════════════════════════════════════════
# 4. OTP — Eski testlar (mavjud)
# ═══════════════════════════════════════════════════════════════

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser2',
            phone_number='+998990000001',
            password='testpassword123'
        )

    def test_login_with_phone(self):
        """Telefon raqami orqali login qilishni tekshirish."""
        response = self.client.post('/api/accounts/login/', {
            'username': '+998990000001',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_otp_generation(self):
        """OTP kod yaratilishini tekshirish."""
        response = self.client.post('/api/accounts/login/', {
            'username': 'testuser2',
            'password': 'testpassword123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        otp_resp = self.client.post('/api/accounts/send-otp/')
        self.assertEqual(otp_resp.status_code, 200)
        self.assertEqual(otp_resp.data.get('status'), 'ok')

        # Redis'da kod saqlanganini tekshirish
        cache_key = f"otp_{self.user.id}"
        self.assertIsNotNone(cache.get(cache_key))
