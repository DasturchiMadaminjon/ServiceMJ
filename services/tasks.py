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
        
    message = (
        f"🚨 <b>YANGI BUYURTMA!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: #{request_id}\n"
        f"📂 Kategoriya: {category_name}\n"
        f"📝 Tavsif: {description}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Admin panel orqali usta biriktiring."
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        return str(e)
