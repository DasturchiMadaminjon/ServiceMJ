"""
accounts/views.py — Autentifikatsiya, Profil va Qurilma boshqaruvi.

Endpointlar:
  POST   /api/accounts/register/         — Ro'yxatdan o'tish
  POST   /api/accounts/login/            — Kirish (JWT + DeviceSession)
  POST   /api/accounts/token/refresh/    — Token yangilash (DeviceSession JTI yangilanadi)
  POST   /api/accounts/logout/           — Joriy qurilmadan chiqish
  POST   /api/accounts/logout-all/       — Barcha qurilmalardan chiqish
  GET    /api/accounts/profile/          — Profilni ko'rish
  PATCH  /api/accounts/profile/          — Profilni yangilash (avatar yuklash)
  POST   /api/accounts/send-otp/         — OTP kodi yuborish
  POST   /api/accounts/verify-otp/       — OTP kodni tasdiqlash
  GET    /api/accounts/devices/          — Faol qurilmalar ro'yxati
  DELETE /api/accounts/devices/<id>/     — Qurilmani o'chirish (sessiyadan chiqish)
"""
import random
import logging

from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseLoginView,
    TokenRefreshView    as BaseRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterSerializer, UserSerializer, DeviceSessionSerializer,
)
from .models import CustomUser, DeviceSession

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Yordamchi funksiyalar (modul darajasida, testlash uchun qulay)
# ──────────────────────────────────────────────────────────────────

def _get_client_ip(request) -> str:
    """Haqiqiy IP manzilni aniqlaydi (reverse proxy orqali ham)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _parse_device_name(user_agent: str) -> str:
    """User-Agent satridan qurilma va brauzer nomini aniqlab, insoniy nom qaytaradi."""
    ua = ua_lower = user_agent.lower()

    device = 'Qurilma'
    for keyword, name in [
        ('iphone',    'iPhone'),
        ('ipad',      'iPad'),
        ('android',   'Android'),
        ('windows',   'Windows'),
        ('macintosh', 'Mac'),
        ('linux',     'Linux'),
    ]:
        if keyword in ua_lower:
            device = name
            break

    browser = 'Brauzer'
    # Edge ni Chrome dan oldin tekshiramiz (Edge UA da ham 'chrome' bor)
    for keyword, name in [
        ('edg/',     'Edge'),
        ('chrome',   'Chrome'),
        ('firefox',  'Firefox'),
        ('safari',   'Safari'),
        ('postman',  'Postman'),
    ]:
        if keyword in ua_lower:
            browser = name
            break

    return f"{device} / {browser}"


def _save_device_session(request, user: CustomUser, refresh_str: str) -> None:
    """
    Login yoki token yangilanishida yangi DeviceSession yozuvi yaratadi.
    Xato bo'lsa — logga yozib, davom etadi (login bloklanmaydi).
    """
    try:
        token_obj   = JWTRefreshToken(refresh_str)
        jti         = token_obj['jti']
        ip          = _get_client_ip(request)
        device_name = _parse_device_name(
            request.META.get('HTTP_USER_AGENT', 'Noma\'lum')
        )
        DeviceSession.objects.create(
            user=user,
            refresh_jti=jti,
            device_name=device_name,
            ip_address=ip,
        )
        logger.info(
            "[AUTH] Yangi qurilma sessiyasi | user=%s | device=%s | ip=%s",
            user.username, device_name, ip
        )
    except Exception as exc:
        logger.warning("[AUTH] DeviceSession yaratishda xato: %s", exc)


# ──────────────────────────────────────────────────────────────────
# Autentifikatsiya Views
# ──────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    Yangi foydalanuvchi ro'yxatdan o'tkazish.

    POST /api/accounts/register/
    Body: { "username", "password", "phone_number", "role" }
    """
    queryset           = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class   = RegisterSerializer


class LoginView(BaseLoginView):
    """
    JWT Login. Muvaffaqiyatli kirishda qurilma sessiyasini ham saqlaydi.
    Telegram kabi — 30 kun davomida qayta login talab qilinmaydi.

    POST /api/accounts/login/
    Body: { "username": "...", "password": "..." }
    Response: { "access": "...", "refresh": "..." }
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            logger.warning(
                "[AUTH] Login muvaffaqiyatsiz | username=%s | ip=%s",
                request.data.get('username', '?'),
                _get_client_ip(request),
            )
            raise

        response_data = serializer.validated_data
        user = serializer.user

        # Qurilma sessiyasini saqlash (Telegram kabi eslab qolish)
        refresh_str = response_data.get('refresh')
        if refresh_str and user:
            _save_device_session(request, user, refresh_str)

        logger.info(
            "[AUTH] Login muvaffaqiyatli | user=%s | ip=%s",
            user.username, _get_client_ip(request),
        )
        return Response(response_data)


class TokenRefreshView(BaseRefreshView):
    """
    JWT Token yangilash. Yangi JTI bilan DeviceSession avtomatik yangilanadi.
    Token rotatsiyasi natijasida eski token blacklistga tushadi — xavfsiz.

    POST /api/accounts/token/refresh/
    Body: { "refresh": "..." }
    Response: { "access": "...", "refresh": "..." }
    """

    def post(self, request, *args, **kwargs):
        # Rotatsiyadan oldin eski JTI ni saqlaymiz
        old_refresh = request.data.get('refresh', '')
        old_jti     = None

        if old_refresh:
            try:
                old_jti = JWTRefreshToken(old_refresh)['jti']
            except Exception:
                pass

        response = super().post(request, *args, **kwargs)

        # Muvaffaqiyatli yangilangan — DeviceSession JTI ni yangilaymiz
        if response.status_code == 200 and old_jti:
            new_refresh = response.data.get('refresh')
            if new_refresh:
                try:
                    new_jti  = JWTRefreshToken(new_refresh)['jti']
                    updated  = DeviceSession.objects.filter(
                        refresh_jti=old_jti
                    ).update(refresh_jti=new_jti)
                    logger.debug(
                        "[AUTH] Token yangilandi | old_jti=%.8s… → new_jti=%.8s… | sessions=%d",
                        old_jti, new_jti, updated,
                    )
                except Exception as exc:
                    logger.warning("[AUTH] DeviceSession JTI yangilashda xato: %s", exc)

        return response


class LogoutView(APIView):
    """
    Joriy qurilmadan chiqish.
    Refresh tokenni blacklist ga qo'shadi va DeviceSession ni o'chiradi.

    POST /api/accounts/logout/
    Body: { "refresh": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'refresh token kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_obj = JWTRefreshToken(refresh_token)
            jti       = token_obj['jti']

            # DeviceSession ni o'chirish
            deleted, _ = DeviceSession.objects.filter(
                user=request.user, refresh_jti=jti
            ).delete()

            # Tokenni blacklist ga qo'shish
            token_obj.blacklist()

            logger.info(
                "[AUTH] Logout | user=%s | sessions_deleted=%d",
                request.user.username, deleted,
            )
            return Response({'detail': 'Muvaffaqiyatli chiqildi.'})

        except TokenError as exc:
            logger.warning("[AUTH] Logout — token xatosi: %s", exc)
            return Response(
                {'detail': 'Token noto\'g\'ri yoki muddati o\'tgan.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutAllView(APIView):
    """
    Barcha qurilmalardan bir vaqtda chiqish.
    Barcha DeviceSession larni o'chiradi va barcha tokenlarni blacklist ga qo'shadi.

    POST /api/accounts/logout-all/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # 1. Barcha DeviceSession larni o'chirish
        deleted, _ = DeviceSession.objects.filter(user=request.user).delete()

        # 2. Barcha outstanding tokenlarni blacklist ga qo'shish
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken, BlacklistedToken,
            )
            outstanding_qs = OutstandingToken.objects.filter(user=request.user)
            for token in outstanding_qs:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as exc:
            logger.warning("[AUTH] Logout-all blacklist xatosi: %s", exc)

        logger.info(
            "[AUTH] Logout-all | user=%s | sessions_deleted=%d",
            request.user.username, deleted,
        )
        return Response(
            {'detail': f'{deleted} ta qurilmadan muvaffaqiyatli chiqildi.'}
        )


# ──────────────────────────────────────────────────────────────────
# Qurilmalar boshqaruvi
# ──────────────────────────────────────────────────────────────────

class DeviceListView(generics.ListAPIView):
    """
    Foydalanuvchining barcha faol qurilmalari (Telegram kabi «Sessiyalar» ro'yxati).

    GET /api/accounts/devices/
    Response: [ { id, device_name, ip_address, last_active, created_at }, ... ]
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = DeviceSessionSerializer

    def get_queryset(self):
        return DeviceSession.objects.filter(user=self.request.user)


class DeviceDeleteView(generics.DestroyAPIView):
    """
    Muayyan qurilmadan (sessiyadan) masofadan chiqish.
    Tokenni ham blacklist ga qo'shadi.

    DELETE /api/accounts/devices/<id>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeviceSession.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        # Tokenni ham blacklist ga qo'shamiz
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken, BlacklistedToken,
            )
            ot = OutstandingToken.objects.filter(jti=instance.refresh_jti).first()
            if ot:
                BlacklistedToken.objects.get_or_create(token=ot)
        except Exception as exc:
            logger.warning("[AUTH] DeviceDelete blacklist xatosi: %s", exc)

        logger.info(
            "[AUTH] Qurilma o'chirildi | user=%s | device=%s | ip=%s",
            instance.user.username, instance.device_name, instance.ip_address,
        )
        instance.delete()


# ──────────────────────────────────────────────────────────────────
# Profil va OTP Views
# ──────────────────────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Joriy foydalanuvchi profili — ko'rish va yangilash.
    Avatar yuklash uchun multipart/form-data ishlatiladi.

    GET   /api/accounts/profile/
    PATCH /api/accounts/profile/
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class   = UserSerializer
    parser_classes     = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class SendOTPView(APIView):
    """
    Telefon raqamni tasdiqlash uchun 6 xonali OTP kodi yuborish.
    Kod Redis da 5 daqiqa saqlanadi.

    TODO: Eskiz yoki Twilio SMS integratsiyasi (hozir simulatsiya rejimi).

    POST /api/accounts/send-otp/
    Response: { "detail": "...", "status": "ok" }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user

        if user.is_verified:
            return Response(
                {'detail': 'Siz allaqachon tasdiqlangansiz.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6 xonali tasodifiy kod (4 xonali eski koddan xavfsizroq)
        otp = str(random.randint(100000, 999999))

        # Redisga 5 daqiqaga saqlash
        cache.set(f"otp_{user.id}", otp, timeout=300)

        # TODO: Haqiqiy SMS yuborish (Eskiz/Twilio integratsiyasi)
        # Hozircha simulatsiya rejimida — kod faqat logda
        logger.debug("[OTP] Mock kod yaratildi | user=%s", user.username)

        return Response({
            'detail': 'Tasdiqlash kodi yuborildi.',
            'status': 'ok',
        })


class VerifyOTPView(APIView):
    """
    OTP kodni tekshirish va akkauntni tasdiqlash.

    POST /api/accounts/verify-otp/
    Body: { "code": "123456" }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {'detail': 'Kod kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_otp = cache.get(f"otp_{user.id}")

        if saved_otp and saved_otp == str(code):
            user.is_verified = True
            user.save()
            cache.delete(f"otp_{user.id}")
            logger.info("[OTP] Tasdiqlandi | user=%s", user.username)
            return Response(
                {'detail': 'Tabriklaymiz! Akkauntingiz muvaffaqiyatli tasdiqlandi.'}
            )

        logger.warning("[OTP] Noto'g'ri kod | user=%s", user.username)
        return Response(
            {'detail': 'Kod noto\'g\'ri yoki muddati o\'tgan.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
