from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceRequest
from .tasks import notify_new_service_request, notify_status_changed


@receiver(post_save, sender=ServiceRequest)
def on_service_request_saved(sender, instance, created, **kwargs):
    if created:
        notify_new_service_request.delay(instance.id)
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            notify_status_changed.delay(instance.id, old_status, instance.status)
