import os
import requests
from dotenv import load_dotenv

# .env faylidan sozlamalarni yuklash
load_dotenv()

API_KEY = os.getenv('INFOBIP_API_KEY', '')
BASE_URL = os.getenv('INFOBIP_BASE_URL', '')

print("=" * 60)
print("INFOBIP SMS YETKAZIB BERISH HISOBOTI (DELIVERY REPORTS)")
print("=" * 60)

if not API_KEY or not BASE_URL:
    print("❌ XATO: INFOBIP_API_KEY yoki INFOBIP_BASE_URL .env faylida topilmadi!")
    exit(1)

# Oxirgi yuborilgan SMS statuslarini olish
url = f"https://{BASE_URL}/sms/2/reports?limit=5"
headers = {
    "Authorization": f"App {API_KEY}",
    "Accept": "application/json"
}

try:
    print("Infobip API'dan hisobotlar olinmoqda...")
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status kod: {r.status_code}")
    print("-" * 60)
    
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        if not results:
            print("ℹ️ Hozircha hech qanday hisobot topilmadi (so'nggi 24 soatda yuborilmagan bo'lishi mumkin).")
        else:
            for i, msg in enumerate(results):
                print(f"Xabar #{i+1}:")
                print(f"  Kimga (To):     {msg.get('to')}")
                print(f"  Yuboruvchi:    {msg.get('from')}")
                print(f"  Sana (Sent At): {msg.get('sentAt')}")
                status = msg.get('status', {})
                print(f"  Status Nomi:    {status.get('name')} (ID: {status.get('id')})")
                print(f"  Tavsif:         {status.get('description')}")
                error = msg.get('error', {})
                if error.get('id') != 0:
                    print(f"  ❌ XATO (Error): {error.get('name')} (ID: {error.get('id')})")
                    print(f"  Xato Sababi:    {error.get('description')}")
                else:
                    print("  ✅ Muvaffaqiyatli yetkazildi (Delivered)")
                print("-" * 60)
    else:
        print(f"❌ XATOLIK: Infobip hisobotlarni qaytarmadi. Response: {r.text}")
except Exception as e:
    print(f"❌ TARMOQ XATOSI: {str(e)}")
print("=" * 60)
