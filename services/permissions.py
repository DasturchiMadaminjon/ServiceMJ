from rest_framework import permissions

class IsClient(permissions.BasePermission):
    """
    Faqat 'client' (mijoz) roli bo'lgan foydalanuvchilar uchun.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'

class IsProvider(permissions.BasePermission):
    """
    Faqat 'provider' (usta) roli bo'lgan foydalanuvchilar uchun.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'provider'

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Obyekt egasi uchun to'liq ruxsat, boshqalar uchun faqat o'qish.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # ServiceRequest egasi mijoz
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        
        # ProviderProfile egasi usta
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False
