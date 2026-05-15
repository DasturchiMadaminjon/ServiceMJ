from django.contrib.auth.models import AbstractUser
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
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']
        )],
        help_text="Profil rasmi. Maksimal 10 MB. Rasm avtomatik siqiladi (WebP, 1200×1200)."
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
