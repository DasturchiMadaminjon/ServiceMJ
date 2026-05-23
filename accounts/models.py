from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client',   'Mijoz'),
        ('provider', 'Usta'),
        ('admin',    'Admin'),
    )

    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified  = models.BooleanField(default=False)
    avatar       = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=[
                'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp',
                'tiff', 'tif', 'heic', 'heif', 'avif',
            ]
        )],
        help_text="Profil rasmi. Maksimal 50 MB. Rasm avtomatik siqiladi (WebP, 2400×2400).",
    )

    class Meta:
        verbose_name        = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_provider(self):
        return self.role == 'provider'

    def save(self, *args, **kwargs):
        # Avatar yuklanganda avtomatik siqish
        if self.pk:
            try:
                old = CustomUser.objects.get(pk=self.pk)
                avatar_changed = old.avatar != self.avatar
            except CustomUser.DoesNotExist:
                avatar_changed = bool(self.avatar)
        else:
            avatar_changed = bool(self.avatar)

        if avatar_changed and self.avatar:
            self._compress_avatar()

        super().save(*args, **kwargs)

    def _compress_avatar(self):
        from .utils import compress_image
        import os
        try:
            content, ext = compress_image(self.avatar)
            base = os.path.splitext(os.path.basename(self.avatar.name))[0]
            new_name = f"{base}.{ext}"
            self.avatar.save(new_name, content, save=False)
        except Exception:
            pass  # Siqish xato bo'lsa asl rasmni saqlaydi


class DeviceSession(models.Model):
    """
    Foydalanuvchining har bir qurilmasi/sessiyasi uchun yozuv.
    Telegram kabi — qurilmadan chiqmasdan qaytib kirish imkonini beradi.
    Token rotatsiyasida refresh_jti avtomatik yangilanadi.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_sessions',
        verbose_name='Foydalanuvchi',
    )
    refresh_jti = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='JWT Token ID',
        help_text='Refresh tokenning JTI claim qiymati. Token rotatsiyasida yangilanadi.',
    )
    device_name = models.CharField(
        max_length=255,
        default="Noma'lum qurilma",
        verbose_name='Qurilma nomi',
        help_text='Masalan: iPhone / Safari, Android / Chrome, Windows / Edge',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP manzil',
    )
    last_active = models.DateTimeField(
        auto_now=True,
        verbose_name='Oxirgi faollik',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana',
    )

    class Meta:
        verbose_name        = "Qurilma Sessiyasi"
        verbose_name_plural = "Qurilma Sessiyalari"
        ordering            = ['-last_active']

    def __str__(self):
        return f"{self.user.username} — {self.device_name} ({self.ip_address})"
