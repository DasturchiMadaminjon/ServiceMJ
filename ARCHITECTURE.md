# ServiceMJ — Loyiha Arxitekturasi 🏗️

Ushbu hujjat loyihaning texnik tuzilishi, modullar orasidagi bog'liqlik va xavfsizlik qoidalarini belgilaydi.

---

## 🚀 Texnologik Stek

| Qatlam | Texnologiya | Versiya |
|--------|-------------|---------|
| **Backend** | Python + Django + DRF | 3.11 / 4.2+ / 3.14+ |
| **Frontend** | Vanilla JS (SPA) + Nginx | — |
| **Kesh & OTP** | Redis | 7+ |
| **Ma'lumotlar bazasi** | PostgreSQL | 15 |
| **Asinxron vazifalar** | Celery | 5+ |
| **Konteynerizatsiya** | Docker + Docker Compose | — |
| **Cloud** | AWS EC2 (Amazon Linux 2023) | — |
| **SSL** | Let's Encrypt (Certbot) | — |
| **Monitoring** | Sentry | — |

---

## 📁 Modullar va Mas'uliyatlar

### 1. `accounts` — Foydalanuvchilar va Autentifikatsiya
- **`CustomUser`**: `phone_number`, `role` (`client`/`provider`), `is_verified` maydonlari bilan kengaytirilgan foydalanuvchi modeli.
- **`DeviceSession`**: Har bir faol qurilma uchun `refresh_jti`, `device_name`, `ip_address` saqlanadi (Telegram kabi persistent auth).
- **JWT auth**: `SimpleJWT` + Token Rotatsiyasi + Blacklist.
- **OTP tizimi**: 6 xonali kod Redis'da 5 daqiqa saqlanadi. Yuborish zanjiri:
  1. `SMS_PROVIDER=infobip` → Infobip SMS API
  2. `SMS_PROVIDER=eskiz` → Eskiz.uz SMS API
  3. `SMS_PROVIDER=none` yoki SMS ishlamasa → Telegram (admin chatga)
  4. Telegram ham ishlamasa → kod `response`'da `otp_code` maydoni sifatida qaytariladi

### 2. `services` — Ustalar va Xizmatlar
- **`Category`**: Ierarxik kategoriyalar (ota-bola).
- **`Skill`**: Ko'nikmalar — kategoriyaga bog'liq.
- **`ProviderProfile`**: Usta profili — `bio`, `experience_years`, `hourly_rate`, `rating`, `is_active`.
- **`PortfolioItem`**: Usta portfeli — rasm va tavsif.
- **`DashboardStatsView`**: Admin uchun statistika endpoint.

### 3. `orders` — Buyurtmalar va Sharhlar
- **`ServiceRequest`**: Mijoz → Usta xizmat so'rovi. Status zanjiri:
  ```
  pending → accepted → in_progress → completed
     ↓           ↓           ↓
  cancelled   cancelled   cancelled
  ```
- **`Review`**: Tugallangan buyurtmalarga sharh va reyting (1–5). Sharh saqlanganda usta reytingi avtomatik qayta hisoblanadi.
- **`logic.py`**: `select_for_update()` orqali Race Condition oldini olish (tranzaksiya darajasida qulflash).

### 4. `frontend` — Statik Fayllar
- `index.html`, `app.js`, `style.css` — Nginx tomonidan to'g'ridan-to'g'ri xizmat qilinadi.

---

## 🔄 Ma'lumot Oqimi (Data Flow)

```
Brauzer/Mobil
     │
     ▼
[Nginx: tadbikor.uz]  ← SSL termination (Let's Encrypt)
     │
     ├──/api/*──────► [Django (Gunicorn)] ◄──► [PostgreSQL]
     │                        │
     │                        ├──► [Redis] ◄──► [Celery Worker]
     │                        │                      │
     │                        │               [Telegram Bot]
     └──/static, /media──► [Nginx static]
```

### OTP Yuborish Zanjiri

```
POST /api/accounts/send-otp/
     │
     ├── SMS_PROVIDER=infobip? ──► Infobip API ──► ✅ yoki ❌
     ├── SMS_PROVIDER=eskiz?   ──► Eskiz.uz API ──► ✅ yoki ❌
     ├── SMS_PROVIDER=none     ──► SMS o'tkazib yuboriladi
     │
     └── SMS yuborilmadimi?
              │
              ├── TELEGRAM_BOT_TOKEN mavjud? ──► Telegram Admin Chat ──► ✅
              └── Telegram ham yo'q?          ──► otp_code response'da qaytadi
```

---

## 🔐 Xavfsizlik Tamoyillari

| Tahdid | Himoya mexanizmi |
|--------|-----------------|
| Token o'g'irlash | JWT + Blacklist + Token Rotatsiyasi |
| Qurilma boshqaruvi | `DeviceSession` — har bir qurilma alohida kuzatiladi |
| Race Condition | `select_for_update()` tranzaksiyasi |
| OTP brute force | Redis TTL (5 daqiqa) + bir martali kod |
| SQL Injection | Django ORM (parametrlangan so'rovlar) |
| CORS | `CORS_ALLOWED_ORIGINS` sozlamasi |
| Maxfiy ma'lumotlar | `.env` fayli, hech qachon kodda yozilmaydi |
| Bot hujumlari | `ALLOWED_HOSTS` + Nginx rate limiting |
| SSL/HTTPS | Let's Encrypt sertifikati |

---

## 🛠️ Admin Panel — Bulk Actions

| Model | Mavjud amallar |
|-------|----------------|
| `CustomUser` | Faollashtirish, bloklash, verification holati |
| `DeviceSession` | Guruhli sessiya tozalash (majburiy logout) |
| `ProviderProfile` | Faollashtirish, o'chirish, reyting qayta hisoblash |
| `ServiceRequest` | Holat boshqaruvi (Cancel, Complete, Reset, In-Progress) |

---

## 🧪 Testlash Strategiyasi (TDD)

Testlar har bir Django app ichida joylashgan:

| Fayl | Testlar | Qamrov |
|------|---------|--------|
| `accounts/tests.py` | 31 ta | Register, Login, OTP, DeviceSession, Token Refresh, Logout, ChangeRole |
| `orders/tests.py` | 48 ta | ServiceRequest CRUD, Status zanjiri, Review, MyRequests |
| `services/tests.py` | 82 ta | Provider, Portfolio, Dashboard, Celery tasks, Stress test, To'liq stsenariy |
| **Jami** | **161 ta** | ~88% qamrov |

**Testlarni ishga tushirish:**
```bash
docker-compose exec web python manage.py test accounts services orders -v 2
```

---

## 📦 Celery Tasklar

| Task | Fayl | Qachon chaqiriladi |
|------|------|-------------------|
| `notify_new_service_request` | `orders/tasks.py` | Yangi buyurtma yaratilganda |
| `notify_status_changed` | `orders/tasks.py` | Buyurtma holati o'zgarganda |
| `send_telegram_notification` | `services/tasks.py` | Admin chatga xabar yuborishda |

---

## 🌐 Deployment

| Resurs | Manzil |
|--------|--------|
| Live server | `https://tadbikor.uz` |
| GitHub | `https://github.com/DasturchiMadaminjon/ServiceHub` |
| Swagger | `https://tadbikor.uz/swagger/` |
| Admin | `https://tadbikor.uz/admin/` |

---

## 📋 O'zgarishlar Tarixi

| Sana | O'zgarish | Muallif |
|------|-----------|---------|
| 2026-04-26 | Loyiha boshlandi | Madaminjon |
| 2026-05-24 | OTP, DeviceSession, JWT qo'shildi | Madaminjon |
| 2026-05-30 | HTTPS (Let's Encrypt), ALLOWED_HOSTS tuzatildi | Madaminjon |
| 2026-06-01 | SMS_PROVIDER zanjiri (Infobip/Eskiz/Telegram/Display) | Madaminjon |
| 2026-06-03 | orders/tests.py to'ldirildi (48 ta test), ChangeRole testlari | Madaminjon |
| 2026-07-03 | swagger_qollanma.md qo'shildi (31 endpoint, O'zbek tili) | Madaminjon |
| 2026-07-03 | API test — 24 endpoint 100% muvaffaqiyat, .gitignore yangilandi | Madaminjon |

---
*Oxirgi yangilanish: 2026-07-03*
