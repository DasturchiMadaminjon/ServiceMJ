from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import CustomUser


class UserRegistrationTest(APITestCase):
    def setUp(self):
        self.url = reverse('register')
        self.client_data = {
            'username': 'testclient',
            'password': 'TestPass123!',
            'phone_number': '998901234567',
            'role': 'client',
        }
        self.provider_data = {
            'username': 'testprovider',
            'password': 'TestPass123!',
            'phone_number': '998907654321',
            'role': 'provider',
        }

    def test_client_registration_success(self):
        r = self.client.post(self.url, self.client_data, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.get().role, 'client')
        self.assertNotIn('password', r.data)

    def test_provider_registration_success(self):
        r = self.client.post(self.url, self.provider_data, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.get().role, 'provider')

    def test_duplicate_username_fails(self):
        self.client.post(self.url, self.client_data, format='json')
        data = self.provider_data.copy()
        data['username'] = 'testclient'
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_phone_fails(self):
        self.client.post(self.url, self.client_data, format='json')
        data = self.provider_data.copy()
        data['phone_number'] = '998901234567'
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_role_fails(self):
        data = self.client_data.copy()
        data['role'] = 'superuser'
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_role_rejected(self):
        data = self.client_data.copy()
        data['role'] = 'admin'
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password_fails(self):
        data = self.client_data.copy()
        data['password'] = '123'
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_username_fails(self):
        data = self.client_data.copy()
        del data['username']
        r = self.client.post(self.url, data, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTest(APITestCase):
    def setUp(self):
        self.url = reverse('token_obtain_pair')
        self.user = CustomUser.objects.create_user(
            username='loginuser', password='loginpass123'
        )

    def test_login_success(self):
        r = self.client.post(self.url, {'username': 'loginuser', 'password': 'loginpass123'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('access', r.data)
        self.assertIn('refresh', r.data)

    def test_login_wrong_password(self):
        r = self.client.post(self.url, {'username': 'loginuser', 'password': 'WRONG'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        r = self.client.post(self.url, {'username': 'nobody', 'password': 'pass'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTest(APITestCase):
    def setUp(self):
        CustomUser.objects.create_user(username='refreshuser', password='refreshpass123')
        login_r = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'refreshuser', 'password': 'refreshpass123'},
            format='json'
        )
        self.refresh_token = login_r.data['refresh']

    def test_token_refresh_success(self):
        r = self.client.post(reverse('token_refresh'), {'refresh': self.refresh_token}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('access', r.data)

    def test_invalid_refresh_token_rejected(self):
        r = self.client.post(reverse('token_refresh'), {'refresh': 'invalid.token'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='profileuser', password='profilepass123', role='client'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        r = self.client.get(reverse('profile'))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['username'], 'profileuser')
        self.assertEqual(r.data['role'], 'client')

    def test_unauthenticated_profile_denied(self):
        self.client.force_authenticate(user=None)
        r = self.client.get(reverse('profile'))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_email(self):
        r = self.client.patch(reverse('profile'), {'email': 'new@test.com'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['email'], 'new@test.com')

    def test_role_is_readonly_in_profile(self):
        r = self.client.patch(reverse('profile'), {'role': 'admin'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['role'], 'client')


# ═══════════════════════════════════════════════
# AVATAR YUKLASH TESTLARI
# ═══════════════════════════════════════════════
import io
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings


def make_image_file(width=100, height=100, fmt='JPEG', size_bytes=None):
    """Test uchun rasm fayl ob'ekti yaratadi."""
    buf = io.BytesIO()
    img = PILImage.new('RGB', (width, height), color=(100, 149, 237))
    img.save(buf, format=fmt)
    if size_bytes:
        # Kerakli hajmga yetkazish uchun padding
        buf.write(b'\x00' * max(0, size_bytes - buf.tell()))
    buf.seek(0)
    ext = fmt.lower().replace('jpeg', 'jpg')
    return SimpleUploadedFile(f'test.{ext}', buf.read(), content_type=f'image/{fmt.lower()}')


class AvatarUploadTest(APITestCase):
    def setUp(self):
        from accounts.models import CustomUser
        self.user = CustomUser.objects.create_user(
            username='avataruser', password='Pass1234!', role='client'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('profile')

    def test_upload_small_jpeg(self):
        """Kichik JPEG rasm muvaffaqiyatli yuklanadi."""
        img_file = make_image_file(200, 200, 'JPEG')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

    def test_upload_png_converted(self):
        """PNG rasm ham qabul qilinadi."""
        img_file = make_image_file(300, 300, 'PNG')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 200)

    def test_large_image_compressed(self):
        """3000×3000 rasm yuklansa, 1200×1200 dan kichik bo'lib saqlanadi."""
        buf = io.BytesIO()
        big_img = PILImage.new('RGB', (3000, 3000), color=(255, 0, 0))
        big_img.save(buf, format='JPEG', quality=95)
        buf.seek(0)
        img_file = SimpleUploadedFile('big.jpg', buf.read(), content_type='image/jpeg')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        if self.user.avatar:
            from PIL import Image as PILImg
            import os, django
            from django.conf import settings as dj_settings
            avatar_path = os.path.join(dj_settings.MEDIA_ROOT, self.user.avatar.name)
            if os.path.exists(avatar_path):
                saved = PILImg.open(avatar_path)
                self.assertLessEqual(saved.width, 1200)
                self.assertLessEqual(saved.height, 1200)

    def test_file_over_10mb_rejected(self):
        """10 MB dan katta fayl 400 qaytaradi."""
        buf = io.BytesIO()
        img = PILImage.new('RGB', (100, 100), color=(0, 255, 0))
        img.save(buf, format='JPEG')
        # 10 MB + 1 byte padding
        big_content = buf.getvalue() + b'\x00' * (10 * 1024 * 1024 + 1)
        img_file = SimpleUploadedFile('big.jpg', big_content, content_type='image/jpeg')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertIn('avatar', r.data)

    def test_avatar_url_in_response(self):
        """Javobda avatar_url maydoni bo'ladi."""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('avatar_url', r.data)

    def test_avatar_not_required(self):
        """Avatar yo'q bo'lsa ham profil ishlaydi."""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data['avatar_url'])

    def test_rgba_image_accepted(self):
        """RGBA (PNG transparency) rasm ham qabul qilinadi."""
        buf = io.BytesIO()
        img = PILImage.new('RGBA', (200, 200), color=(0, 100, 200, 128))
        img.save(buf, format='PNG')
        buf.seek(0)
        img_file = SimpleUploadedFile('rgba.png', buf.read(), content_type='image/png')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_cannot_upload(self):
        """Autentifikatsiyasiz rasm yuklab bo'lmaydi."""
        self.client.force_authenticate(user=None)
        img_file = make_image_file(100, 100, 'JPEG')
        r = self.client.patch(self.url, {'avatar': img_file}, format='multipart')
        self.assertEqual(r.status_code, 401)
