# 🏛 ServiceHub.uz — Tizim Arxitekturasi va Texnik Hujjatlash

Ushbu hujjat ServiceHub.uz loyihasining ichki tuzilishi, ma'lumotlar bazasi sxemasi va komponentlararo aloqalarni tushuntiradi. Loyiha **Clean Architecture** va **Modular Monolith** tamoyillari asosida qurilgan.

---

## 1. Ma'lumotlar Bazasi Sxemasi (ER Diagram)

Baza tuzilishi foydalanuvchi rollari va xizmatlar zanjirini samarali boshqarishga qaratilgan.

```mermaid
erDiagram
    USER ||--o| PROVIDER_PROFILE : "has"
    USER ||--o{ SERVICE_REQUEST : "creates"
    CATEGORY ||--o{ CATEGORY : "parent_of"
    CATEGORY ||--o{ SERVICE_REQUEST : "belongs_to"
    
    USER {
        int id
        string username
        string phone_number
        string role "client/provider/admin"
        boolean is_verified
    }
    
    PROVIDER_PROFILE {
        int id
        int user_id
        text bio
        int experience_years
        decimal rating
    }
    
    CATEGORY {
        int id
        string name
        int parent_id
    }
    
# 🧬 ServiceHub — Genetik Arxitektura va Texnik Spesifikatsiya

Ushbu hujjat ServiceHub loyihasining "ichki dunyosi" — ma'lumotlar oqimi, xavfsizlik qatlamlari va integratsiya mantiqini 100% tiklash uchun mo'ljallangan.

---

## 1. Ma'lumotlar Bazasi Sxemasi (ERD Mantiqi)

Loyiha PostgreSQL relyatsion MB dan foydalanadi. Asosiy obyektlar bog'liqligi:

### A. Accounts App (Foydalanuvchilar)
- **CustomUser**: `AbstractUser` vorisi.
    - `role`: `client` | `provider` | `admin`
    - `phone_number`: Unique (E.164 formati)
    - `is_verified`: SMS orqali tasdiqlash uchun (kelajakda).

### B. Services App (Biznes Mantiq)
- **Category**: Daraxtsimon (Self-referencing ForeignKey) struktura.
- **ProviderProfile**: `User` bilan OneToOne.
    - `skills`: ManyToMany with `Skill`
    - `portfolio_items`: OneToMany with `Portfolio`
- **ServiceRequest**: Markaziy tranzaksiya modeli.
    - `status`: State machine (Pending -> Accepted -> In Progress -> Completed -> Cancelled)
    - `customer`: ForeignKey (User)
    - `provider`: ForeignKey (ProviderProfile)
- **Review**: `ServiceRequest` bilan OneToOne. Faqat `status='completed'` bo'lganda yaratiladi.

---

## 2. Xavfsizlik va Autentifikatsiya (JWT Layer)

Loyiha **Stateless Authentication** tamoyiliga asoslangan.
- **Header**: `Authorization: Bearer <access_token>`
- **Refresh Flow**: `api/accounts/token/refresh/` end-point orqali sessiyani uzaytirish.
- **Role-Based Access Control (RBAC)**:
    - Mijozlar faqat o'z buyurtmalarini ko'radi.
    - Ustalar barcha "Pending" buyurtmalarni va faqat o'ziga biriktirilgan buyurtmalarni ko'radi.
    - Adminlar barcha amallarga ega.

---

## 3. Asinxron Tizim (Celery + Redis)

Og'ir vazifalar va bildirishnomalar fonda bajariladi:
- **Broker**: Redis (`6379-port`).
- **Worker**: `celery -A config worker -l info`
- **Logic**: Yangi buyurtma yaratilganda `services.signals` orqali `send_telegram_notification.delay()` vazifasi navbatga qo'yiladi.

---

## 4. Konteynerizatsiya (Docker Blueprint)

Tizim 3 ta asosiy xizmatdan iborat:
1. **db**: PostgreSQL 15-ALPINE.
2. **redis**: Redis 7-ALPINE.
3. **web**: Python 3.10-SLIM based Django app.
    - Port: `8000`
    - Gunicorn server (`worker=3`) orqali xizmat ko'rsatadi.

---

## 5. TDD (Test Driven Development) Standarti

Loyiha 100% test qamroviga ega bo'lishi uchun quyidagi qoidalar amal qiladi:
- **Test Command**: `python manage.py test services.test_api_tdd`
- **Isolation**: Har bir test o'zining "In-Memory" bazasida ishlaydi.
- **Mocking**: Tashqi API (Telegram) so'rovlari `unittest.mock` yordamida simulyatsiya qilinadi.

---

## 6. Kelajakdagi Evolyutsiya (DNA Extension)
- **SMS Gateway**: `is_verified` maydonini ishlatish uchun.
- **Geolokatsiya**: `PostGIS` orqali eng yaqin ustani topish.
- **Payment System**: Click/Payme orqali tranzaksiyalarni boshqarish.

---
*Ushbu arxitektura o'zgarmas (Genetic) qoidalarga asoslangan bo'lib, loyihaning miqyoslanishini kafolatlaydi.*

Loyihani kelajakda qanday kengaytirish mumkin?
- **Microservices:** Agar foydalanuvchilar soni milliondan oshsa, `accounts` va `services` modullarini alohida servis qilib ajratish mumkin.
- **Load Balancing:** Nginx orqali bir nechta Django konteynerlariga yuklamani taqsimlash mumkin.
---
*Tayyorladi: ServiceHub.uz Development Team (AI Powered)*
