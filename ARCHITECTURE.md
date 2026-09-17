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
- `index.html` — Asosiy SPA. **Auth oynasi (`page-auth`)** birinchi ko'rinadi.
- `app.js` — Barcha biznes mantig'i. `DOMContentLoaded` da token yo'q bo'lsa `showPage('auth')` chaqiriladi.
- `style.css` — Barcha stillar.
- `geo-metric-92a207.html` — Yer o'lchash dasturi (yangi tabda ochiladi).
- `neuromind_ultimate_v3.html` — Xotira rivojlantirish dasturi (yangi tabda ochiladi).

### 5. `nginx/` — Nginx Konfiguratsiyasi
- `default.conf` — Asosiy konfiguratsiya:
  - `/api/*` → Django (Gunicorn, port 8000)
  - `/admin/*`, `/swagger/*` → Django
  - `/geo-metric-92a207.html`, `/neuromind_ultimate_v3.html` → To'g'ridan fayl
  - `location /` → `try_files $uri $uri/ /index.html` (SPA routing)

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
     ├──/media/*────► [Nginx /var/www/media/]
     ├──/*.html─────► [Nginx /var/www/frontend/]  ← geo-metric, neuromind
     └──/──────────► [Nginx → index.html]  ← Auth oynasi ko'rinadi
```

### ⚠️ Auth Ko'rinish Mexanizmi
1. Foydalanuvchi `tadbikor.uz` ga kiradi
2. Nginx `try_files` → `index.html` beradi
3. `app.js` `DOMContentLoaded` ishga tushadi
4. `localStorage` da token yo'q → `showPage('auth')` → Registratsiya/Login oynasi ko'rinadi
5. Token mavjud → `initApp()` → Asosiy sahifa ko'rinadi


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
| Frontend Double-Submit | `isCreatingRequest` bayrog'i orqali tugmalarni qulflash |

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
| `services/tests.py` | 93 ta | Provider, Portfolio, Dashboard, Celery tasks, Stress test, **Frontend fayllar (11 ta yangi)** |
| **Jami** | **172 ta** | ~90% qamrov |

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
| GitHub | `https://github.com/DasturchiMadaminjon/ServiceMJ` |
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
| 2026-07-03 | Frontend: Double-submit himoyasi, Backend: Deploy script tuzatildi | Madaminjon |
| 2026-07-28 | Sentry DisallowedHost xatolari bartaraf etildi, ALLOWED_HOSTS va CSRF moslashtirildi, ortiqcha subdomenlar olib tashlandi | Madaminjon |
| 2026-08-30 | Frontend UI yangilandi: "Qo'shimcha" menyusi (Yer o'lchash, Xotira) va Ustalar sahifasiga Kategoriya filtri qo'shildi | Madaminjon |
| 2026-08-30 | Bloklangan foydalanuvchi uchun login xatosiga Telegram admin linki (@Madaminjon01) qo'shildi | Madaminjon |
| 2026-09-17 | Nginx konfiguratsiyasi (nginx/default.conf) qo'shildi — Auth oynasi muammosi hal qilindi | Madaminjon |
| 2026-09-17 | TDD: FrontendFilesTest (11 ta test) qo'shildi — index.html, app.js, nginx integratsiyasi | Madaminjon |

---
*Oxirgi yangilanish: 2026-09-17*
