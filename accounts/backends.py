from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser

class PhoneOrUsernameBackend(ModelBackend):
    """
    Foydalanuvchini ham username, ham telefon raqami orqali topishga imkon beruvchi backend.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Username yoki telefon raqami bo'yicha qidirish
            user = CustomUser.objects.get(Q(username=username) | Q(phone_number=username))
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None
        return None
