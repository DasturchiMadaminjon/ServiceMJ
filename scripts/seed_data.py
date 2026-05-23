"""
scripts/seed_data.py — Dastlabki kategoriya va ko'nikmalar ma'lumotlarini bazaga yuklash.

Ishlatish (Docker ichida):
    docker-compose exec web python scripts/seed_data.py

Yoki manage.py shell orqali:
    docker-compose exec web python manage.py shell < scripts/seed_data.py
"""
import os
import sys
import django

# Django sozlamalarini yuklash
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.models import Category, Skill

# ─── KATEGORIYALAR VA KO'NIKMALAR ──────────────────────────────────────────────
DATA = [
    {
        "name": "Dasturchilik",
        "icon": "💻",
        "skills": [
            "Python dasturlash",
            "JavaScript / TypeScript",
            "Django / FastAPI backend",
            "React / Vue.js frontend",
            "Mobile ilova (Flutter)",
            "Android (Kotlin/Java)",
            "iOS (Swift)",
            "Ma'lumotlar bazasi (PostgreSQL, MySQL)",
            "DevOps / Docker / CI-CD",
            "Bot yaratish (Telegram)",
            "1C dasturlash",
            "Web-sayt yaratish",
            "API integratsiya",
        ],
    },
    {
        "name": "Dizayn",
        "icon": "🎨",
        "skills": [
            "Logo va brend dizayn",
            "UI/UX dizayn",
            "Figma / Adobe XD",
            "Grafik dizayn",
            "Motion dizayn / animatsiya",
            "Banner va reklama dizayn",
            "SMM uchun kontent dizayn",
            "3D modellashtirish",
            "Foto montaj",
            "Video montaj",
        ],
    },
    {
        "name": "Ustachilik",
        "icon": "🛠️",
        "skills": [
            "Santexnik",
            "Elektrik montaj",
            "Konditsioner o'rnatish",
            "Sovutgich ta'mirlash",
            "Kir yuvish mashinasi ta'mirlash",
            "Mebel yig'ish",
            "Qulf va eshik ta'mirlash",
            "Kafel yotqizish",
            "Gips-karton ishlari",
            "Bo'yoq ishlari",
        ],
    },
    {
        "name": "Qurilish",
        "icon": "🏗️",
        "skills": [
            "Umumiy qurilish",
            "Poydevor qurilish",
            "Tom yopish",
            "Devor g'ishtlash",
            "Taxta-yogʻoch ishlari",
            "Temir konstruksiyalar",
            "Havza va basseyn",
            "Hashar ishlari",
        ],
    },
    {
        "name": "Ta'lim va Repetitorlik",
        "icon": "📚",
        "skills": [
            "Matematika o'qitish",
            "Ingliz tili",
            "Rus tili",
            "Maktab fanlaridan repetitor",
            "Kompyuter savodxonligi",
            "Kasbiy kurslar (onlayn)",
            "Musiqa o'rgatish",
            "Rasm chizish o'rgatish",
            "Yoga va meditatsiya",
        ],
    },
    {
        "name": "Yuk tashish",
        "icon": "🚚",
        "skills": [
            "Kichik yuk tashish (gazel)",
            "O'rta yuk tashish",
            "Ko'chirish xizmati",
            "Xalqaro yuk tashish",
            "Mebel ko'chirish",
            "Muzlatgichli yuk",
        ],
    },
    {
        "name": "Tozalash",
        "icon": "🧹",
        "skills": [
            "Uyni tozalash",
            "Ofisni tozalash",
            "Kanal va quvur tozalash",
            "Gilam yuvish",
            "Deraza yuvish",
            "Qurilishdan keyin tozalash",
            "Dezinfeksiya",
        ],
    },
    {
        "name": "Bog'dorchilik",
        "icon": "🌿",
        "skills": [
            "Bog' parvarishi",
            "O'simlik kesish",
            "Maysa ekish / archa",
            "Peyzaj dizayn",
            "Sug'orish tizimi o'rnatish",
        ],
    },
    {
        "name": "Sog'liq va Go'zallik",
        "icon": "💆",
        "skills": [
            "Massaj",
            "Sartaroshlik",
            "Soch bo'yash va parvarishlash",
            "Manikur / Pedikur",
            "Qosh va kirpik",
            "Kelin-kuyov makiyaji",
            "Tibbiy muolaja (uyda)",
        ],
    },
    {
        "name": "Boshqa xizmatlar",
        "icon": "🔧",
        "skills": [
            "Tarjimonlik",
            "Huquqiy maslahat",
            "Buxgalteriya",
            "Fotograf",
            "Videograf",
            "Event menejment",
            "Hayvon parvarishi",
            "Savdo menejeri",
        ],
    },
]


def run():
    created_cats  = 0
    created_skills = 0
    skipped = 0

    for item in DATA:
        cat, cat_created = Category.objects.get_or_create(
            name=item["name"],
            defaults={"icon": item.get("icon", ""), "parent": None},
        )
        if cat_created:
            created_cats += 1
            print(f"  [YANGI] Kategoriya: {cat.name}")
        else:
            print(f"  [MAVJUD] Kategoriya: {cat.name}")

        for skill_name in item["skills"]:
            skill, skill_created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": cat},
            )
            if skill_created:
                created_skills += 1
            else:
                skipped += 1

    print("\n" + "=" * 50)
    print(f"[OK] Yangi kategoriyalar: {created_cats}")
    print(f"[OK] Yangi ko'nikmalar:   {created_skills}")
    print(f"[--] Allaqachon mavjud:   {skipped}")
    print("=" * 50)
    print("Seed data muvaffaqiyatli yuklandi!")


if __name__ == "__main__":
    run()
