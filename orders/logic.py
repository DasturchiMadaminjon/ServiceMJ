import logging
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from .models import ServiceRequest

logger = logging.getLogger(__name__)

def update_request_status(request_id: int, user, new_status: str) -> ServiceRequest:
    """
    So'rov statusini o'zgartiradi. 
    Race condition larning oldini olish uchun bazani qulflaydi (select_for_update).
    Millionlab so'rovlar kelganda ham bitta so'rovni ikki kishi o'zgartira olmaydi.
    """
    with transaction.atomic():
        # select_for_update() yordamida qatorni qulflaymiz
        try:
            instance = ServiceRequest.objects.select_for_update().get(id=request_id)
        except ServiceRequest.DoesNotExist:
            raise ValidationError("Xizmat so'rovi topilmadi.")

        if not instance.can_transition_to(new_status):
            raise ValidationError(f"'{instance.status}' holatidan '{new_status}' holatiga o'tish mumkin emas.")

        # Eski statusni eslab qolamiz (signal uchun kerak bo'lishi mumkin)
        instance._old_status = instance.status

        # Ruxsatlarni tekshirish
        if new_status == 'accepted':
            if not hasattr(user, 'role') or user.role != 'provider':
                raise PermissionDenied("Faqat usta qabul qila oladi.")
            instance.provider = user

        elif new_status in ('in_progress', 'completed'):
            if instance.provider != user and not user.is_staff:
                raise PermissionDenied("Faqat tayinlangan usta holat o'zgartira oladi.")

        elif new_status == 'cancelled':
            if instance.customer != user and instance.provider != user and not user.is_staff:
                raise PermissionDenied("Bekor qilish uchun ruxsat yo'q.")

        # Yangilash va saqlash
        instance.status = new_status
        instance.save()
        
        logger.info(
            "[ORDERS] Status o'zgartirildi | req_id=%d | old=%s | new=%s | user=%s",
            instance.id, instance._old_status, new_status, user.username
        )
        return instance
