import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_telegram_notification(self, message: str):
    """Telegramda adminlarga bildirishnoma yuborish."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_ADMIN_CHAT_IDS', [])

    if not token or not chat_ids:
        logger.warning("Telegram sozlamalari topilmadi. Xabar yuborilmadi.")
        return {"status": "skipped", "reason": "no credentials"}

    results = []
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(
                url,
                json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'},
                timeout=10
            )
            resp.raise_for_status()
            results.append({'chat_id': chat_id, 'status': 'sent'})
            logger.info(f"Telegram xabar yuborildi: {chat_id}")
        except requests.RequestException as exc:
            logger.error(f"Telegram xato ({chat_id}): {exc}")
            results.append({'chat_id': chat_id, 'status': 'error', 'error': str(exc)})
            try:
                self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error(f"Maksimal qayta urinishlar tugadi: {chat_id}")

    return {"status": "done", "results": results}


