import os
import requests
from celery import shared_task
from django.conf import settings

@shared_task
def send_telegram_notification(request_id, category_name, description):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    
    if not bot_token or not chat_id:
        return "Telegram credentials not found"
        
    chat_ids = chat_id.split(',')
    
    message = (
        f"🚨 <b>YANGI BUYURTMA!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: #{request_id}\n"
        f"📂 Kategoriya: {category_name}\n"
        f"📝 Tavsif: {description}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Admin panel orqali usta biriktiring."
    )
    
    results = []
    for cid in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': cid.strip(),
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=payload)
            results.append(response.json())
        except Exception as e:
            results.append(str(e))
    return results
