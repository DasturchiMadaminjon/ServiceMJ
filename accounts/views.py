import random
from django.core.cache import cache
from rest_framework.views import APIView
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
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class   = UserSerializer
    parser_classes     = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class SendOTPView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        if user.is_verified:
            return Response({"detail": "Siz allaqachon tasdiqlangansiz."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 4 xonali tasodifiy kod yaratish
        otp = str(random.randint(1000, 9999))
        
        # Redisga 5 daqiqaga saqlash
        cache.set(f"otp_{user.id}", otp, timeout=300)
        
        # SIMULATSIYA: Haqiqiy SMS o'rniga kodni logga chiqaramiz va javobda yuboramiz
        print(f"\n[SMS SIMULATSIYA] Foydalanuvchi {user.username} uchun kod: {otp}\n")
        
        return Response({
            "detail": "Tasdiqlash kodi yuborildi (Simulatsiya).",
            "mock_code": otp  # Test rejimida kodni ochiq yuboramiz
        })


class VerifyOTPView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        code = request.data.get('code')
        
        if not code:
            return Response({"detail": "Kod kiritilmagan."}, status=status.HTTP_400_BAD_REQUEST)
        
        saved_otp = cache.get(f"otp_{user.id}")
        
        if saved_otp and saved_otp == str(code):
            user.is_verified = True
            user.save()
            cache.delete(f"otp_{user.id}")
            return Response({"detail": "Tabriklaymiz! Akkauntingiz muvaffaqiyatli tasdiqlandi."})
        
        return Response({"detail": "Kod noto'g'ri yoki muddati o'tgan."}, status=status.HTTP_400_BAD_REQUEST)
