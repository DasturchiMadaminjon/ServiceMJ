from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser

class PhoneOrUsernameBackend(ModelBackend):
    """
    Foydalanuvchini ham username, ham telefon raqami orqali topishga imkon beruvchi backend.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Username (iexact - case-insensitive) yoki telefon raqami bo'yicha qidirish
            user = CustomUser.objects.filter(
                Q(username__iexact=username) | Q(phone_number=username)
            ).first()
            
            if user and user.check_password(password):
                return user
        except Exception:
            return None
        return None
