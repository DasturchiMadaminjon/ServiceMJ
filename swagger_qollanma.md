# tadbikor.uz/swagger/ — Barcha Endpointlar To'liq Qo'llanmasi

## 🔑 AVVAL QILISH KERAK: Authorize (Tizimga kirish)

**Swagger da qulfli endpointlarni sinash uchun quyidagi qadamlarni bajaring:**

1. `POST /api/accounts/register/` orqali yangi hisob yarating (quyida ko'rsatilgan)
2. `POST /api/accounts/login/` orqali kirng va `access` tokenni nusxalang
3. Swagger sahifaning **yuqori o'ng** tomonidagi **`Authorize 🔒`** tugmasini bosing
4. Ochilgan oynaga quyidagicha yozing (boshida `Bearer ` so'zi va bitta bo'sh joy bo'lishi shart):
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR....(token)
   ```
5. **`Authorize`** tugmasini bosing → **`Close`** bosing
6. Endi barcha qulfli endpointlar ishlaydi ✅

---

## 👤 1-BO'LIM: ACCOUNTS (Foydalanuvchilar)

### Endpoint 1 — `POST /api/accounts/register/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **URL** | `/api/accounts/register/` |
| **Auth kerakmi?** | ❌ Yo'q (Ochiq) |
| **Vazifasi** | Yangi foydalanuvchi ro'yxatdan o'tkazadi |
| **Qayerda ishlatiladi** | Yangi foydalanuvchi birinchi marta kira olganda |
| **Muvaffaqiyatli javob** | `201 Created` |

**Try it out → Request body ga yoziladi:**
```json
{
  "username": "ali_ustaman",
  "password": "MyPass123!",
  "phone_number": "+998901234567",
  "role": "provider",
  "email": "ali@gmail.com"
}
```
> `role` faqat `"client"` yoki `"provider"` bo'lishi mumkin.

---

### Endpoint 2 — `POST /api/accounts/login/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **URL** | `/api/accounts/login/` |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Tizimga kiradi va JWT token beradi |
| **Muvaffaqiyatli javob** | `200 OK` + `access` va `refresh` tokenlar |

**Request body:**
```json
{
  "username": "ali_ustaman",
  "password": "MyPass123!"
}
```
> ⚠️ **Muhim:** Login `email` bilan EMAS, faqat `username` yoki `phone_number` bilan ishlaydi!
> Bu `PhoneOrUsernameBackend` custom autentifikatsiya tizimi orqali ta'minlangan.

---

### Endpoint 3 — `POST /api/accounts/token/refresh/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **URL** | `/api/accounts/token/refresh/` |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Eskirgan `access` tokenni yangilaydi |
| **Qachon ishlatiladi** | Access token 5 daqiqada eskiradi, refresh bilan yangilanadi |

**Request body:**
```json
{
  "refresh": "eyJhbGci...(refresh token)"
}
```

---

### Endpoint 4 — `POST /api/accounts/logout/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak (Bearer token) |
| **Vazifasi** | Faqat joriy qurilmadan chiqish |
| **Muvaffaqiyatli javob** | `200 OK` |

**Request body:**
```json
{
  "refresh": "eyJhbGci...(refresh token)"
}
```

---

### Endpoint 5 — `POST /api/accounts/logout-all/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Barcha qurilmalardan bir vaqtda chiqish (masalan, telefon yo'qolsa) |
| **Muvaffaqiyatli javob** | `200 OK` |

**Request body bo'sh `{}` yoki `refresh` bilan:**
```json
{}
```

---

### Endpoint 6 — `GET /api/accounts/profile/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Kirgan foydalanuvchining profil ma'lumotlarini ko'rsatadi |
| **Muvaffaqiyatli javob** | `200 OK` + id, username, email, role, phone_number, is_verified |

> Request body kerak emas, shunchaki `Execute` bosing.

---

### Endpoint 7 — `PATCH /api/accounts/profile/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | PATCH |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Profil ma'lumotlarini yangilash |

**Request body (faqat o'zgartirmoqchi bo'lgan maydon):**
```json
{
  "email": "yangi_email@gmail.com",
  "phone_number": "+998991234567"
}
```

---

### Endpoint 8 — `POST /api/accounts/change-role/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | `client` dan `provider` ga yoki teskari o'tish |

**Request body:**
```json
{
  "role": "provider"
}
```

---

### Endpoint 9 — `POST /api/accounts/send-otp/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Telefon raqamni tasdiqlash uchun SMS kod yuboradi |

**Request body:**
```json
{
  "phone_number": "+998901234567"
}
```

---

### Endpoint 10 — `POST /api/accounts/verify-otp/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | SMS dan kelgan kodni kiritib telefon raqamni tasdiqlaydi |

**Request body:**
```json
{
  "otp_code": "123456"
}
```

---

### Endpoint 11 — `GET /api/accounts/devices/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Foydalanuvchi kirgan barcha qurilmalar ro'yxatini ko'rsatadi |

> Request body kerak emas.

---

### Endpoint 12 — `DELETE /api/accounts/devices/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | DELETE |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Ma'lum qurilmani majburan chiqarish (Force Logout) |
| **`{id}` ga nima yoziladi** | `GET /devices/` dan kelgan qurilma `id` raqami |

---

## 🛠️ 2-BO'LIM: SERVICES (Xizmatlar)

### Endpoint 13 — `GET /api/services/categories/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Barcha xizmat kategoriyalari ro'yxati (santexnik, elektrchi va h.k.) |

> Request body kerak emas, shunchaki `Execute`.

---

### Endpoint 14 — `GET /api/services/categories/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Bitta kategoriyaning batafsil ma'lumoti |
| **`{id}` ga nima yoziladi** | Kategoriya raqami, masalan: `1` |

---

### Endpoint 15 — `GET /api/services/skills/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Barcha ko'nikmalar ro'yxati |

---

### Endpoint 16 — `GET /api/services/providers/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Barcha ro'yxatdan o'tgan ustalar ro'yxati |

---

### Endpoint 17 — `POST /api/services/providers/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak (`provider` roli bo'lgan foydalanuvchi) |
| **Vazifasi** | Yangi usta profili yaratish |

**Request body (`bio` ixtiyoriy, `hourly_rate` ixtiyoriy):**
```json
{
  "bio": "10 yillik tajribali santexnikman",
  "experience_years": 5,
  "hourly_rate": "50000.00",
  "skill_ids": [1, 2]
}
```
> ⚠️ **Eslatma:** `city` va `currency` maydoni `ProviderProfile` modelida mavjud emas!
> ⚠️ Bir foydalanuvchi faqat **bitta** profil yarata oladi. Ikkinchi marta yuborilsa `400` xato beradi.

---

### Endpoint 18 — `GET /api/services/providers/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Bitta ustaning profil ma'lumoti (reyting, bio, portfel) |
| **`{id}` ga nima yoziladi** | Usta profil raqami, masalan: `1` |

---

### Endpoint 19 — `PUT/PATCH /api/services/providers/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | PUT yoki PATCH |
| **Auth kerakmi?** | ✅ Kerak (o'z profili) |
| **Vazifasi** | Usta profilini yangilash |

**PATCH (faqat kerakli maydon):**
```json
{
  "bio": "15 yillik tajribali santexnikman",
  "hourly_rate": "75000.00"
}
```

---

### Endpoint 20 — `GET /api/services/providers/{id}/portfolio/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ❌ Yo'q |
| **Vazifasi** | Ustaning portfolio ishlari ro'yxati |
| **`{id}` ga nima yoziladi** | Usta profil raqami |

---

### Endpoint 21 — `POST /api/services/providers/{id}/portfolio/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Ustaning portfolio ga yangi ish qo'shish |

**Request body:**
```json
{
  "title": "Vannaxonani ta'mirlash",
  "description": "3 xonali uyda to'liq santexnik ta'mirot",
  "cost": "500000.00"
}
```

---

### Endpoint 22 — `GET /api/services/dashboard/stats/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak (Faqat **Admin**) |
| **Vazifasi** | Umumiy statistika: foydalanuvchilar soni, buyurtmalar, daromad |

---

## 📦 3-BO'LIM: ORDERS (Buyurtmalar)

### Endpoint 23 — `GET /api/orders/requests/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Barcha buyurtmalar ro'yxati (admin uchun — hammasi, mijoz uchun — o'ziniki) |

---

### Endpoint 24 — `POST /api/orders/requests/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **URL** | `/api/orders/requests/` |
| **Auth kerakmi?** | ✅ Kerak (`client` roli) |
| **Vazifasi** | Yangi xizmat buyurtmasi yaratish |

**Request body:**
```json
{
  "provider": 1,
  "category": 1,
  "description": "Hammomda kran almashtirib berasizmi?",
  "address": "Toshkent, Yunusobod, 14-mavze",
  "budget": "150000.00",
  "currency": "UZS"
}
```
> ⚠️ **Muhim:** `provider` maydoniga `GET /providers/` dan kelgan `user.id` (integer) yoziladi.
> `ProviderProfile.id` emas — foydalanuvchining `User.id` si!
> Misol: `GET /providers/` javobi `{"id": 2, "user": {"id": 1, ...}}` bo'lsa, `provider: 1` yoziladi.

---

### Endpoint 25 — `GET /api/orders/requests/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Bitta buyurtmaning batafsil ma'lumoti va holati |
| **`{id}` ga nima yoziladi** | Buyurtma raqami, masalan: `1` |

---

### Endpoint 26 — `PATCH /api/orders/requests/{id}/status/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | PATCH |
| **Auth kerakmi?** | ✅ Kerak (Usta yoki admin) |
| **Vazifasi** | Buyurtma holatini o'zgartirish |

**Holat zanjiri:** `pending` → `accepted` → `in_progress` → `completed`

**Request body:**
```json
{
  "status": "accepted"
}
```
> Ruxsat etilgan o'tishlar: `pending→accepted/cancelled`, `accepted→in_progress/cancelled`, `in_progress→completed/cancelled`

---

### Endpoint 27 — `GET /api/orders/my-requests/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Faqat **mening** buyurtmalarim (boshqalarniki ko'rinmaydi) |

---

### Endpoint 28 — `GET /api/orders/reviews/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Barcha sharhlar ro'yxati |

---

### Endpoint 29 — `POST /api/orders/reviews/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | POST |
| **Auth kerakmi?** | ✅ Kerak (`client` roli, faqat `completed` buyurtma uchun) |
| **Vazifasi** | Xizmat sifatini baholash va sharh qoldirish |

**Request body:**
```json
{
  "service_request": 1,
  "rating": 5,
  "comment": "Juda zo'r usta, ishni sifatli bajardi!"
}
```
> `service_request` holati `completed` bo'lishi shart, aks holda xato beradi.

---

### Endpoint 30 — `GET /api/orders/reviews/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | GET |
| **Auth kerakmi?** | ✅ Kerak |
| **Vazifasi** | Bitta sharhning batafsil ma'lumoti |

---

### Endpoint 31 — `DELETE /api/orders/reviews/{id}/`
| Maydon | Ma'lumot |
|--------|----------|
| **Metod** | DELETE |
| **Auth kerakmi?** | ✅ Kerak (o'z sharhi yoki admin) |
| **Vazifasi** | Sharhni o'chirish |

---

## 🗺️ TO'LIQ SWAGGER ISHLATISH YO'L XARITASI

```
1. Register (yangi hisob yarating)
       ↓
2. Login (access + refresh token oling)
       ↓
3. Authorize tugmasi → "Bearer <access_token>" kiriting
       ↓
4. GET /categories/ → kategoriya ID larini bilib oling
5. GET /providers/  → usta ID larini bilib oling
       ↓
6. POST /orders/requests/ → buyurtma yarating (provider + category ID bilan)
       ↓
7. PATCH /orders/requests/{id}/status/ → holat o'zgartiring
       ↓
8. POST /orders/reviews/ → sharh qoldiring (status=completed bo'lgandan keyin)
```
