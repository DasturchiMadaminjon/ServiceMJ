from rest_framework import permissions


class IsClient(permissions.BasePermission):
    """Faqat 'client' roli uchun ruxsat."""
    message = "Bu amalni faqat mijozlar (client) bajarishi mumkin."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )


class IsProvider(permissions.BasePermission):
    """Faqat 'provider' roli uchun ruxsat."""
    message = "Bu amalni faqat ustalar (provider) bajarishi mumkin."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'provider'
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Ob'ekt egasi yoki admin uchun ruxsat."""
    message = "Siz bu ob'ektni o'zgartira olmaysiz."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        for attr in ('user', 'customer', 'reviewer'):
            if hasattr(obj, attr) and getattr(obj, attr) == request.user:
                return True
        return False
