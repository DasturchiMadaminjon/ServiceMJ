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


@shared_task
def notify_new_service_request(request_id: int):
    """Yangi xizmat so'rovi haqida adminlarga xabar."""
    from services.models import ServiceRequest
    try:
        req = ServiceRequest.objects.select_related('customer', 'category').get(id=request_id)
        cat_name = req.category.name if req.category else "Noma'lum"
        msg = (
            f"🔔 <b>Yangi xizmat so'rovi #{req.id}</b>\n"
            f"👤 Mijoz: {req.customer.username}\n"
            f"📂 Kategoriya: {cat_name}\n"
            f"📝 Tavsif: {req.description[:200]}\n"
            f"💰 Byudjet: {req.budget or 'Kelishiladi'}"
        )
        send_telegram_notification.delay(msg)
    except ServiceRequest.DoesNotExist:
        logger.error(f"ServiceRequest #{request_id} topilmadi")


@shared_task
def notify_status_changed(request_id: int, old_status: str, new_status: str):
    """Status o'zgarishi haqida xabar."""
    from services.models import ServiceRequest
    try:
        req = ServiceRequest.objects.select_related('customer', 'provider').get(id=request_id)
        status_emoji = {
            'accepted':    '✅',
            'in_progress': '🔧',
            'completed':   '🎉',
            'cancelled':   '❌',
        }
        emoji = status_emoji.get(new_status, '📋')
        prov_name = req.provider.username if req.provider else "Yo'q"
        msg = (
            f"{emoji} <b>So'rov #{req.id} holati o'zgardi</b>\n"
            f"📊 {old_status} → {new_status}\n"
            f"👤 Mijoz: {req.customer.username}\n"
            f"🔧 Usta: {prov_name}"
        )
        send_telegram_notification.delay(msg)
    except ServiceRequest.DoesNotExist:
        logger.error(f"ServiceRequest #{request_id} topilmadi")
