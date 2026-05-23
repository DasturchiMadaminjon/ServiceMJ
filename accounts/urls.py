from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    LogoutAllView,
    ProfileView,
    SendOTPView,
    VerifyOTPView,
    DeviceListView,
    DeviceDeleteView,
    ChangeRoleView,
)

urlpatterns = [
    # ── Ro'yxatdan o'tish ──────────────────────────────────────────
    path('register/',       RegisterView.as_view(),     name='register'),

    # ── Autentifikatsiya ───────────────────────────────────────────
    path('login/',          LoginView.as_view(),         name='token_obtain_pair'),
    path('token/refresh/',  TokenRefreshView.as_view(),  name='token_refresh'),
    path('logout/',         LogoutView.as_view(),         name='logout'),
    path('logout-all/',     LogoutAllView.as_view(),      name='logout_all'),

    # ── Profil ─────────────────────────────────────────────────────
    path('profile/',        ProfileView.as_view(),        name='profile'),
    path('change-role/',    ChangeRoleView.as_view(),     name='change_role'),

    # ── OTP tasdiqlash ─────────────────────────────────────────────
    path('send-otp/',       SendOTPView.as_view(),        name='send_otp'),
    path('verify-otp/',     VerifyOTPView.as_view(),      name='verify_otp'),

    # ── Qurilmalar boshqaruvi (Telegram kabi sessiyalar) ───────────
    path('devices/',            DeviceListView.as_view(),    name='device_list'),
    path('devices/<int:pk>/',   DeviceDeleteView.as_view(),  name='device_delete'),
]
