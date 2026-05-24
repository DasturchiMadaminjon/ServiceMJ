# ServiceMJ — Loyiha Arxitekturasi 🏗️

Ushbu hujjat loyihaning texnik tuzilishi, modullar orasidagi bog'liqlik va xavfsizlik qoidalarini belgilaydi.

## 🚀 Texnologik Stek
- **Backend:** Django 4.2 + Django REST Framework
- **Frontend:** Vanilla JS (SPA) + Nginx
- **Kesh & OTP:** Redis
- **Ma'lumotlar bazasi:** PostgreSQL 15
- **Infrastruktura:** Docker Compose

## 📁 Modullar va Mas'uliyatlar
1. **`accounts`**: Foydalanuvchilar, profil boshqaruvi, qurilmalar va OTP (SMS) autentifikatsiyasi. Token rotatsiyasida xavfsizlikni ta'minlash uchun **`DeviceSession`** modeli orqali har bir faol qurilmaning IP manzili, `device_name` va `refresh_jti` qiymatlari saqlanadi.
2. **`services`**: Ustalar (Providers), ko'nikmalar (Skills), kategoriya va portfolioni boshqarish.
3. **`orders`**: Mijozlar va ustalar orasidagi xizmat so'rovlari (ServiceRequest) va sharhlar (Review). Tranzaksiyalar yordamida qulflash (select_for_update) va holat boshqaruvi.
4. **`frontend`**: Statik fayllar (index.html, app.js, style.css).

## 🔐 Xavfsizlik Tamoyillari
- **OTP Verification:** Telefon raqamini tasdiqlash Redis orqali 6 xonali kod bilan amalga oshiriladi (ishlab chiqish/test muhitida simulyatsiya uchun `mock_code` taqdim etiladi).
- **Token Rotation & Device Session Blacklist:** Foydalanuvchi tizimdan chiqqanda (`logout`), refresh token blacklistga qo'shiladi va u bilan bog'liq `DeviceSession` majburiy o'chiriladi (Force Logout).
- **No-Cache Policy:** API so'rovlari Nginx darajasida keshlanishi taqiqlangan.
- **Auth:** JWT (SimpleJWT) orqali autentifikatsiya.

## 🛠️ Admin Panel va Boshqaruv (Bulk Actions)
Admin paneldagi boshqaruv samaradorligini oshirish uchun barcha muhim bo'limlarga maxsus **guruhli amallar (Bulk Actions)** integratsiya qilingan:
- **Foydalanuvchilar (`CustomUser`):** Guruhli faollashtirish, bloklash (superuser himoyasi bilan) va verification statuslarini o'zgartirish.
- **Qurilma Sessiyalari (`DeviceSession`):** Tanlangan sessiyalarni guruhli tozalash (majburiy logout).
- **Usta Profillari (`ProviderProfile`):** Guruhli faollashtirish, o'chirish va reytinglarni qayta hisoblash/yangilash.
- **Buyurtmalar (`ServiceRequest`):** So'rovlar holatini guruhli boshqarish (Cancel, Complete, Reset-to-Pending, In-Progress) va rangli status badgelari.

## 🧪 Testlash Strategiyasi (TDD)
Har bir muhim mantiq uchun `tests/` papkasida quyidagi testlar bo'lishi shart:
- `test_auth.py`: Login, OTP mantiqi va DeviceSession token rotatsiyasi testi.
- `test_portfolio.py`: Fayllar yuklanishi va tahrirlanishi.
- `test_orders.py`: Buyurtma yaratish va statuslar o'zgarishi.

---
*Oxirgi yangilanish: 2026-05-24*
