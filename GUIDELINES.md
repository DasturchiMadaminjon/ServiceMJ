# ServiceHub Project Guidelines & Best Practices

Ushbu hujjat loyihaning barqarorligini va sifatini ta'minlash uchun asosiy qoidalar to'plamidir.

## 1. 🛡 TDD (Test Driven Development)
*   **Qoida:** Har qanday yangi funksiya yoki mantiq qo'shishdan oldin, uning testi yozilishi shart.
*   **Maqsad:** Kodda "mantiqiy teshiklar" qolmasligini ta'minlash.
*   **Tekshiruv:** Fayl o'zgarganda `tests/` papkasidagi barcha testlar 100% o'tishi kerak.

## 2. 🧩 Modulli Arxitektura
*   Har bir modul (indicator, telegram, database) faqat bitta vazifa uchun javobgar bo'lsin.
*   Modullar bir-birining ichki ishiga aralashmasligi, faqat API/Interface orqali gaplashishi kerak.

## 3. 📝 Hujjatlashtirish (Documentation)
*   `README.md` — Loyihani ishga tushirish bo'yicha qo'llanma.
*   `ARCHITECTURE.md` — Loyihaning "yo'l xaritasi" va mantiqiy bog'liqliklari.
*   Har bir katta o'zgarishdan keyin ushbu fayllar yangilab turilishi shart.

## 4. 🪵 Loglar va Monitoring
*   Dasturning har bir muhim nuqtasida loglar qoldirilishi kerak.
*   Xatolarni aniqlashda loglar birinchi raqamli "ko'z" vazifasini o'taydi.

## 5. 🔄 Iterativ Sinov (Run-Test-Fix)
1.  Kod yozish.
2.  Terminalda tekshirish.
3.  Xatolarni o'qish va tahlil qilish.
4.  Tuzatib, qayta tekshirish.

## 6. 🧠 Chain of Thought (Fikrlar Zanjiri)
*   Kod yozishdan oldin har doim reja tuziladi va foydalanuvchiga tushuntiriladi.
*   Muammo mayda bo'laklarga bo'linadi.

---
*Ushbu ko'rsatmalar loyihaning "Genetik Kodi" hisoblanadi.*
