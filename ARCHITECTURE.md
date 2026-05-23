# ServiceMJ — Loyiha Arxitekturasi 🏗️

Ushbu hujjat loyihaning texnik tuzilishi, modullar orasidagi bog'liqlik va xavfsizlik qoidalarini belgilaydi.

## 🚀 Texnologik Stek
- **Backend:** Django 4.2 + Django REST Framework
- **Frontend:** Vanilla JS (SPA) + Nginx
- **Kesh & OTP:** Redis
- **Ma'lumotlar bazasi:** PostgreSQL 15
- **Infrastruktura:** Docker Compose

## 📁 Modullar va Mas'uliyatlar
1. **`accounts`**: Foydalanuvchilar, profil boshqaruvi, qurilmalar va OTP (SMS) autentifikatsiyasi.
2. **`services`**: Ustalar (Providers), ko'nikmalar (Skills), kategoriya va portfolioni boshqarish.
3. **`orders`**: Mijozlar va ustalar orasidagi xizmat so'rovlari (ServiceRequest) va sharhlar (Review). Tranzaksiyalar yordamida qulflash (select_for_update) va holat boshqaruvi.
4. **`frontend`**: Statik fayllar (index.html, app.js, style.css).

## 🔐 Xavfsizlik Tamoyillari
- **OTP Verification:** Telefon raqamini tasdiqlash Redis orqali 4 xonali kod bilan amalga oshiriladi.
- **No-Cache Policy:** API so'rovlari Nginx darajasida keshlanishi taqiqlangan.
- **Auth:** JWT (SimpleJWT) orqali autentifikatsiya.

## 🧪 Testlash Strategiyasi (TDD)
Har bir muhim mantiq uchun `tests/` papkasida quyidagi testlar bo'lishi shart:
- `test_auth.py`: Login va OTP mantiqi.
- `test_portfolio.py`: Fayllar yuklanishi va tahrirlanishi.
- `test_orders.py`: Buyurtma yaratish va statuslar o'zgarishi.

---
*Oxirgi yangilanish: 2026-05-16*
