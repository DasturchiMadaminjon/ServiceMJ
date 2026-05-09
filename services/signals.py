from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceRequest
from .tasks import send_telegram_notification

@receiver(post_save, sender=ServiceRequest)
def notify_on_new_request(sender, instance, created, **kwargs):
    if created:
        # Yangi buyurtma yaratilganda Telegramga xabar yuborish
        send_telegram_notification.delay(
            instance.id,
            instance.category.name if instance.category else "Noma'lum",
            instance.description[:100]
        )
