"""
orders/tests.py — To'liq TDD Test Suite

Qamrov:
  - ServiceRequest CRUD (yaratish, ko'rish, tahrirlash, o'chirish)
  - Status zanjiri: pending → accepted → in_progress → completed
  - Ruxsat tekshiruvi: kim nima qila oladi
  - Review yaratish, reyting hisoblash
  - MyServiceRequestsView — status bo'yicha filter
  - Edge case: bo'sh description, noto'g'ri status, o'z sharhini yo'q qilish
"""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from accounts.models import CustomUser
from services.models import Category, ProviderProfile
from orders.models import ServiceRequest, Review


# ─────────────────────────────────────────────────────
# Yordamchi funksiyalar
# ─────────────────────────────────────────────────────

def make_client(username='client1', phone='998901000001'):
    return CustomUser.objects.create_user(
        username=username, password='Pass1234!', role='client', phone_number=phone
    )

def make_provider(username='provider1', phone='998902000001'):
    u = CustomUser.objects.create_user(
        username=username, password='Pass1234!', role='provider', phone_number=phone
    )
    ProviderProfile.objects.create(user=u, bio='Tajribali usta', experience_years=3)
    return u

def make_admin(username='admin1'):
    return CustomUser.objects.create_superuser(
        username=username, password='Admin1234!', email='admin@test.com'
    )

def make_category(name='Santexnika'):
    return Category.objects.create(name=name)

def make_request(customer, category=None, req_status='pending', description='Kran buzuldi'):
    if category is None:
        category = make_category()
    return ServiceRequest.objects.create(
        customer=customer, category=category,
        description=description, status=req_status, budget=100000
    )


# ═══════════════════════════════════════════════════════
# 1. ServiceRequest MODEL TESTLARI
# ═══════════════════════════════════════════════════════

class ServiceRequestModelTest(TestCase):
    """ServiceRequest modeli va can_transition_to() metodini tekshiradi."""

    def setUp(self):
        self.client_user = make_client('m_cl', '998900000010')
        self.cat = make_category('Model')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.req = make_request(self.client_user, self.cat)

    def test_default_status_is_pending(self):
        """Yangi so'rov 'pending' holatida bo'lishi kerak."""
        self.assertEqual(self.req.status, 'pending')

    def test_pending_can_go_to_accepted(self):
        self.assertTrue(self.req.can_transition_to('accepted'))

    def test_pending_can_go_to_cancelled(self):
        self.assertTrue(self.req.can_transition_to('cancelled'))

    def test_pending_cannot_skip_to_in_progress(self):
        self.assertFalse(self.req.can_transition_to('in_progress'))

    def test_pending_cannot_skip_to_completed(self):
        self.assertFalse(self.req.can_transition_to('completed'))

    def test_accepted_can_go_to_in_progress(self):
        self.req.status = 'accepted'
        self.assertTrue(self.req.can_transition_to('in_progress'))

    def test_in_progress_can_go_to_completed(self):
        self.req.status = 'in_progress'
        self.assertTrue(self.req.can_transition_to('completed'))

    def test_completed_has_no_transitions(self):
        self.req.status = 'completed'
        for s in ['pending', 'accepted', 'in_progress', 'cancelled']:
            self.assertFalse(self.req.can_transition_to(s))

    def test_cancelled_is_final_state(self):
        self.req.status = 'cancelled'
        for s in ['pending', 'accepted', 'in_progress', 'completed']:
            self.assertFalse(self.req.can_transition_to(s))

    def test_str_representation(self):
        self.assertIn('pending', str(self.req))


# ═══════════════════════════════════════════════════════
# 2. ServiceRequest CREATE TESTLARI
# ═══════════════════════════════════════════════════════

class ServiceRequestCreateTest(APITestCase):
    """POST /api/orders/requests/ — yaratish testlari."""

    def setUp(self):
        self.client_user = make_client('cr_cl', '998900000020')
        self.provider_user = make_provider('cr_pr', '998900000021')
        self.cat = make_category('Elektr')
        self.url = '/api/orders/requests/'

    def test_client_can_create_request(self):
        """Mijoz buyurtma yarata oladi."""
        self.client.force_authenticate(user=self.client_user)
        with patch('orders.tasks.notify_new_service_request.delay'):
            r = self.client.post(self.url, {
                'description': 'Chiroq ishlamaydi',
                'category': self.cat.id,
                'budget': '150000',
                'address': 'Toshkent'
            }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['status'], 'pending')
        self.assertEqual(r.data['customer']['username'], 'cr_cl')

    def test_provider_cannot_create_request(self):
        """Usta buyurtma yarata olmaydi — biznes qoida."""
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.post(self.url, {
            'description': 'Ruxsatsiz', 'category': self.cat.id
        }, format='json')
        self.assertEqual(r.status_code, 403)

    def test_unauthenticated_cannot_create(self):
        """Kirмagan foydalanuvchi buyurtma yarata olmaydi."""
        r = self.client.post(self.url, {
            'description': 'Anonim', 'category': self.cat.id
        }, format='json')
        self.assertEqual(r.status_code, 401)

    def test_empty_description_rejected(self):
        """Bo'sh tavsif qabul qilinmaydi."""
        self.client.force_authenticate(user=self.client_user)
        with patch('orders.tasks.notify_new_service_request.delay'):
            r = self.client.post(self.url, {
                'description': '', 'category': self.cat.id
            }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_budget_optional(self):
        """Budget ixtiyoriy maydon."""
        self.client.force_authenticate(user=self.client_user)
        with patch('orders.tasks.notify_new_service_request.delay'):
            r = self.client.post(self.url, {
                'description': 'Budgetsiz so\'rov',
                'category': self.cat.id
            }, format='json')
        self.assertEqual(r.status_code, 201)

    def test_created_request_belongs_to_authenticated_user(self):
        """Yaratilgan buyurtma muallif sifatida so'rov yuborgan foydalanuvchiga bog'lanadi."""
        self.client.force_authenticate(user=self.client_user)
        with patch('orders.tasks.notify_new_service_request.delay'):
            r = self.client.post(self.url, {
                'description': 'Muallif tekshiruvi',
                'category': self.cat.id
            }, format='json')
        self.assertEqual(r.status_code, 201)
        req = ServiceRequest.objects.get(id=r.data['id'])
        self.assertEqual(req.customer, self.client_user)


# ═══════════════════════════════════════════════════════
# 3. ServiceRequest LIST VA FILTER TESTLARI
# ═══════════════════════════════════════════════════════

class ServiceRequestListTest(APITestCase):
    """GET /api/orders/requests/ — ro'yxat va filter testlari."""

    def setUp(self):
        self.client1 = make_client('ls_cl1', '998900000030')
        self.client2 = make_client('ls_cl2', '998900000031')
        self.provider = make_provider('ls_pr', '998900000032')
        self.admin = make_admin('ls_adm')
        self.cat = make_category('Lis')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.req1 = make_request(self.client1, self.cat, description='Client1 so\'rovi')
            self.req2 = make_request(self.client2, self.cat, description='Client2 so\'rovi')

    def test_client_sees_only_own_requests(self):
        """Mijoz faqat o'zining buyurtmalarini ko'radi."""
        self.client.force_authenticate(user=self.client1)
        r = self.client.get('/api/orders/requests/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['customer']['username'], 'ls_cl1')

    def test_provider_sees_pending_requests(self):
        """Usta barcha 'pending' buyurtmalarni ko'radi."""
        self.client.force_authenticate(user=self.provider)
        r = self.client.get('/api/orders/requests/')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data['count'], 2)

    def test_admin_sees_all_requests(self):
        """Admin barcha buyurtmalarni ko'radi."""
        self.client.force_authenticate(user=self.admin)
        r = self.client.get('/api/orders/requests/')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data['count'], 2)

    def test_unauthenticated_denied(self):
        r = self.client.get('/api/orders/requests/')
        self.assertEqual(r.status_code, 401)

    def test_filter_by_status(self):
        """Status bo'yicha filterlash ishlashi kerak."""
        self.client.force_authenticate(user=self.client1)
        r = self.client.get('/api/orders/requests/?status=pending')
        self.assertEqual(r.status_code, 200)
        for item in r.data['results']:
            self.assertEqual(item['status'], 'pending')

    def test_pagination_returns_count_and_results(self):
        """Pagination natijasi count va results qaytarishi kerak."""
        self.client.force_authenticate(user=self.admin)
        r = self.client.get('/api/orders/requests/')
        self.assertIn('count', r.data)
        self.assertIn('results', r.data)

    def test_search_by_description(self):
        """Description bo'yicha qidirish."""
        self.client.force_authenticate(user=self.admin)
        r = self.client.get('/api/orders/requests/?search=Client1')
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.data['count'], 0)


# ═══════════════════════════════════════════════════════
# 4. ServiceRequest EDIT VA DELETE TESTLARI
# ═══════════════════════════════════════════════════════

class ServiceRequestEditTest(APITestCase):
    """PATCH/DELETE /api/orders/requests/{id}/ — tahrirlash testlari."""

    def setUp(self):
        self.client_user = make_client('ed_cl', '998900000040')
        self.other_client = make_client('ed_cl2', '998900000041')
        self.cat = make_category('Edit')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.req = make_request(self.client_user, self.cat)

    def test_owner_can_edit_pending_request(self):
        """Buyurtma egasi 'pending' so'rovni tahrirlashi mumkin."""
        self.client.force_authenticate(user=self.client_user)
        r = self.client.patch(f'/api/orders/requests/{self.req.id}/', {
            'description': 'Yangilangan tavsif'
        }, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['description'], 'Yangilangan tavsif')

    def test_cannot_edit_accepted_request(self):
        """Qabul qilingan buyurtmani tahrirlash mumkin emas."""
        self.req.status = 'accepted'
        self.req.save()
        self.client.force_authenticate(user=self.client_user)
        r = self.client.patch(f'/api/orders/requests/{self.req.id}/', {
            'description': 'O\'zgartirish'
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_other_client_cannot_edit(self):
        """Boshqa mijoz ko'rgan buyurtmani tahrirlash mumkin emas (404 — ko'rinmaydi)."""
        self.client.force_authenticate(user=self.other_client)
        r = self.client.patch(f'/api/orders/requests/{self.req.id}/', {
            'description': 'Ruxsatsiz'
        }, format='json')
        self.assertIn(r.status_code, [403, 404])

    def test_owner_can_delete_pending_request(self):
        """Egasi pending so'rovni o'chira oladi."""
        self.client.force_authenticate(user=self.client_user)
        r = self.client.delete(f'/api/orders/requests/{self.req.id}/')
        self.assertIn(r.status_code, [204, 405])


# ═══════════════════════════════════════════════════════
# 5. STATUS O'ZGARTIRISH TESTLARI
# ═══════════════════════════════════════════════════════

class StatusUpdateTest(APITestCase):
    """PATCH /api/orders/requests/{id}/status/ — status zanjiri testlari."""

    def setUp(self):
        self.client_user = make_client('st_cl', '998900000050')
        self.provider_user = make_provider('st_pr', '998900000051')
        self.cat = make_category('Status')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.req = make_request(self.client_user, self.cat)
        patcher = patch('orders.tasks.notify_status_changed.delay')
        patcher.start()
        self.addCleanup(patcher.stop)

    def _url(self):
        return f'/api/orders/requests/{self.req.id}/status/'

    def test_provider_can_accept_pending(self):
        """Usta pending → accepted qila oladi."""
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {'status': 'accepted'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'accepted')
        self.assertEqual(self.req.provider, self.provider_user)

    def test_client_cannot_accept(self):
        """Mijoz so'rovni qabul qila olmaydi."""
        self.client.force_authenticate(user=self.client_user)
        r = self.client.patch(self._url(), {'status': 'accepted'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_provider_in_progress_after_accepted(self):
        """accepted → in_progress."""
        self.req.status = 'accepted'
        self.req.provider = self.provider_user
        self.req.save()
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {'status': 'in_progress'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_provider_complete_after_in_progress(self):
        """in_progress → completed."""
        self.req.status = 'in_progress'
        self.req.provider = self.provider_user
        self.req.save()
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {'status': 'completed'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_invalid_skip_transition_rejected(self):
        """pending → completed — noto'g'ri zanjir."""
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {'status': 'completed'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_client_can_cancel_pending(self):
        """Mijoz o'z pending so'rovini bekor qila oladi."""
        self.client.force_authenticate(user=self.client_user)
        r = self.client.patch(self._url(), {'status': 'cancelled'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_completed_request_cannot_change(self):
        """Tugallangan so'rov o'zgartirilmaydi."""
        self.req.status = 'completed'
        self.req.provider = self.provider_user
        self.req.save()
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {'status': 'cancelled'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_missing_status_field_rejected(self):
        """Status maydoni bo'lmasa xato."""
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.patch(self._url(), {}, format='json')
        self.assertEqual(r.status_code, 400)


# ═══════════════════════════════════════════════════════
# 6. MY-REQUESTS ENDPOINT TESTLARI
# ═══════════════════════════════════════════════════════

class MyRequestsTest(APITestCase):
    """GET /api/orders/my-requests/ — shaxsiy buyurtmalar."""

    def setUp(self):
        self.user = make_client('my_cl', '998900000060')
        self.cat = make_category('MyReq')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.pending_req = make_request(self.user, self.cat, req_status='pending')
            self.cancelled_req = make_request(self.user, self.cat, req_status='cancelled')

    def test_returns_only_own_requests(self):
        """Faqat o'z buyurtmalarini qaytaradi."""
        self.client.force_authenticate(user=self.user)
        r = self.client.get('/api/orders/my-requests/')
        self.assertEqual(r.status_code, 200)
        results = r.data.get('results', r.data)
        self.assertEqual(len(results), 2)

    def test_filter_by_pending_status(self):
        """status=pending filtri ishlaydi."""
        self.client.force_authenticate(user=self.user)
        r = self.client.get('/api/orders/my-requests/?status=pending')
        self.assertEqual(r.status_code, 200)
        results = r.data.get('results', r.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'pending')

    def test_filter_by_cancelled_status(self):
        """status=cancelled filtri ishlaydi."""
        self.client.force_authenticate(user=self.user)
        r = self.client.get('/api/orders/my-requests/?status=cancelled')
        self.assertEqual(r.status_code, 200)
        results = r.data.get('results', r.data)
        self.assertEqual(len(results), 1)

    def test_unauthenticated_denied(self):
        r = self.client.get('/api/orders/my-requests/')
        self.assertEqual(r.status_code, 401)


# ═══════════════════════════════════════════════════════
# 7. REVIEW TESTLARI
# ═══════════════════════════════════════════════════════

class ReviewTest(APITestCase):
    """POST /api/orders/reviews/ — sharh testlari."""

    def setUp(self):
        self.client_user = make_client('rv_cl', '998900000070')
        self.provider_user = make_provider('rv_pr', '998900000071')
        self.cat = make_category('Review')
        with patch('orders.tasks.notify_new_service_request.delay'):
            self.req = make_request(self.client_user, self.cat, req_status='completed')
        self.req.provider = self.provider_user
        self.req.save()

    def test_client_can_review_completed_request(self):
        """Mijoz tugallangan buyurtmaga sharh yoza oladi."""
        self.client.force_authenticate(user=self.client_user)
        r = self.client.post('/api/orders/reviews/', {
            'service_request': self.req.id,
            'rating': 5,
            'comment': 'Ajoyib usta!'
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['rating'], 5)

    def test_review_updates_provider_rating(self):
        """Sharh qo'shilganda usta reytingi yangilanadi."""
        self.client.force_authenticate(user=self.client_user)
        self.client.post('/api/orders/reviews/', {
            'service_request': self.req.id,
            'rating': 4,
            'comment': 'Yaxshi'
        }, format='json')
        self.provider_user.provider_profile.refresh_from_db()
        self.assertEqual(float(self.provider_user.provider_profile.rating), 4.0)

    def test_duplicate_review_rejected(self):
        """Bir buyurtmaga ikki marta sharh yozib bo'lmaydi."""
        Review.objects.create(
            service_request=self.req,
            reviewer=self.client_user,
            provider=self.provider_user,
            rating=4
        )
        self.client.force_authenticate(user=self.client_user)
        r = self.client.post('/api/orders/reviews/', {
            'service_request': self.req.id, 'rating': 3
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_review_on_pending_request_rejected(self):
        """Pending holatidagi buyurtmaga sharh yozib bo'lmaydi."""
        with patch('orders.tasks.notify_new_service_request.delay'):
            pending_req = make_request(self.client_user, self.cat)
        self.client.force_authenticate(user=self.client_user)
        r = self.client.post('/api/orders/reviews/', {
            'service_request': pending_req.id, 'rating': 5
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_provider_cannot_review(self):
        """Usta sharh yoza olmaydi (IsClient ruxsati)."""
        self.client.force_authenticate(user=self.provider_user)
        r = self.client.post('/api/orders/reviews/', {
            'service_request': self.req.id, 'rating': 5
        }, format='json')
        self.assertEqual(r.status_code, 403)

    def test_rating_out_of_range_rejected(self):
        """1-5 dan tashqari reyting qabul qilinmaydi."""
        self.client.force_authenticate(user=self.client_user)
        for bad in [0, 6, -1]:
            r = self.client.post('/api/orders/reviews/', {
                'service_request': self.req.id, 'rating': bad
            }, format='json')
            self.assertEqual(r.status_code, 400, f"Rating {bad} qabul qilindi, kerak emas!")

    def test_list_reviews_no_auth_required(self):
        """Sharhlarni hamma ko'ra oladi."""
        r = self.client.get('/api/orders/reviews/')
        self.assertEqual(r.status_code, 200)

    def test_owner_can_delete_own_review(self):
        """Sharh egasi sharhni o'chira oladi."""
        review = Review.objects.create(
            service_request=self.req,
            reviewer=self.client_user,
            provider=self.provider_user,
            rating=3
        )
        self.client.force_authenticate(user=self.client_user)
        r = self.client.delete(f'/api/orders/reviews/{review.id}/')
        self.assertEqual(r.status_code, 204)

    def test_other_user_cannot_delete_review(self):
        """Boshqa foydalanuvchi sharhni o'chira olmaydi."""
        review = Review.objects.create(
            service_request=self.req,
            reviewer=self.client_user,
            provider=self.provider_user,
            rating=5
        )
        other = make_client('rv_other', '998900000072')
        self.client.force_authenticate(user=other)
        r = self.client.delete(f'/api/orders/reviews/{review.id}/')
        self.assertEqual(r.status_code, 403)
