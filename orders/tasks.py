import logging
from celery import shared_task
from services.tasks import send_telegram_notification

logger = logging.getLogger(__name__)


@shared_task
def notify_new_service_request(request_id: int):
    """Yangi xizmat so'rovi haqida adminlarga xabar."""
    from orders.models import ServiceRequest
    try:
        req = ServiceRequest.objects.select_related('customer', 'category').get(id=request_id)
        cat_name = req.category.name if req.category else "Noma'lum"
        budget_val = "Kelishiladi"
        if req.budget:
            symbol = "so'm" if req.currency == 'UZS' else "USD"
            budget_val = f"{req.budget} {symbol}"

        msg = (
            f"🔔 <b>Yangi xizmat so'rovi #{req.id}</b>\n"
            f"👤 Mijoz: {req.customer.username}\n"
            f"📂 Kategoriya: {cat_name}\n"
            f"📝 Tavsif: {req.description[:200]}\n"
            f"💰 Byudjet: {budget_val}"
        )
        send_telegram_notification.delay(msg)
    except ServiceRequest.DoesNotExist:
        logger.error(f"ServiceRequest #{request_id} topilmadi")


@shared_task
def notify_status_changed(request_id: int, old_status: str, new_status: str):
    """Status o'zgarishi haqida xabar."""
    from orders.models import ServiceRequest
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
