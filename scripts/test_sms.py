import os
import requests
from dotenv import load_dotenv

# .env faylidan sozlamalarni yuklash
load_dotenv()

API_KEY = os.getenv('INFOBIP_API_KEY', '')
BASE_URL = os.getenv('INFOBIP_BASE_URL', '')
SENDER = os.getenv('INFOBIP_SENDER', 'InfoSMS')
TEST_PHONE = "+998915054701" # Sinov telefon raqami

print("=" * 60)
print("INFOBIP SMS INTEGRATSIYA SINOVI")
print("=" * 60)
print(f"Base URL: {BASE_URL}")
print(f"API Key:  {API_KEY[:10]}...{API_KEY[-10:] if len(API_KEY) > 10 else ''}")
print(f"Sender:   {SENDER}")
print(f"Phone:    {TEST_PHONE}")
print("-" * 60)

if not API_KEY or not BASE_URL:
    print("❌ XATO: INFOBIP_API_KEY yoki INFOBIP_BASE_URL .env faylida topilmadi!")
    exit(1)

url = f"https://{BASE_URL}/sms/2/text/advanced"
headers = {
    "Authorization": f"App {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
body = {
    "messages": [
        {
            "destinations": [
                {
                    "to": TEST_PHONE
                }
            ],
            "from": SENDER,
            "text": "ServiceMJ: Infobip SMS tizimi muvaffaqiyatli sinovdan o'tdi! Kod: 999999"
        }
    ]
}

try:
    print("Infobip API'ga so'rov yuborilmoqda...")
    r = requests.post(url, json=body, headers=headers, timeout=10)
    print(f"Status kod: {r.status_code}")
    print(f"Javob matni (JSON): {r.text}")
    print("-" * 60)
    if r.status_code in [200, 201, 202]:
        print("✅ MUVAFFAQIYATLI: SMS muvaffaqiyatli qabul qilindi!")
    else:
        print("❌ XATOLIK: Infobip SMS yuborishni rad etdi. Response kodini tekshiring.")
except Exception as e:
    print(f"❌ TARMOQ XATOSI: {str(e)}")
print("=" * 60)
