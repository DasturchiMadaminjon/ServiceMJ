from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import RegisterSerializer, UserSerializer
from .models import CustomUser


class RegisterView(generics.CreateAPIView):
    queryset           = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class   = RegisterSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/accounts/profile/  — profilni ko'rish
    PUT/PATCH                    — profilni yangilash (avatar bilan)

    Avatar yuklash uchun Content-Type: multipart/form-data ishlatilsin.
    Rasm avtomatik siqiladi: WebP formatiga, maksimal 1200×1200 px.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class   = UserSerializer
    parser_classes     = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True   # PATCH kabi ishlaydi (PUT ham partial)
        return super().update(request, *args, **kwargs)
