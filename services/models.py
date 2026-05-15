from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    icon = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='skills'
    )

    class Meta:
        verbose_name = "Ko'nikma"
        verbose_name_plural = "Ko'nikmalar"

    def __str__(self):
        return self.name


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_profile'
    )
    bio = models.TextField(blank=True, default='')
    experience_years = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='providers')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Usta Profili"
        verbose_name_plural = "Usta Profillari"

    def __str__(self):
        return f"Usta: {self.user.username}"

    def update_rating(self):
        from django.db.models import Avg
        reviews = self.user.received_reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(avg=Avg('rating'))['avg']
            self.rating = round(avg, 2)
            self.save(update_fields=['rating'])


class PortfolioItem(models.Model):
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='portfolio_items'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(
        upload_to='portfolio/',
        null=True, blank=True,
        help_text='Portfolio rasmi. Maksimal 10 MB. Avtomatik siqiladi.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Portfolio"
        verbose_name_plural = "Portfolio Elementlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider.user.username} - {self.title}"

    def save(self, *args, **kwargs):
        if self.image:
            self._compress_image()
        super().save(*args, **kwargs)

    def _compress_image(self):
        from accounts.utils import compress_image
        import os
        try:
            content, ext = compress_image(self.image)
            base = os.path.splitext(os.path.basename(self.image.name))[0]
            self.image.save(f"{base}.{ext}", content, save=False)
        except Exception:
            pass


class ServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending',     'Kutilmoqda'),
        ('accepted',    'Qabul qilindi'),
        ('in_progress', 'Jarayonda'),
        ('completed',   'Tugallandi'),
        ('cancelled',   'Bekor qilindi'),
    )

    STATUS_FLOW = {
        'pending':     ['accepted', 'cancelled'],
        'accepted':    ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
        'completed':   [],
        'cancelled':   [],
    }

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_requests'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='provider_requests'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.CharField(max_length=255, blank=True, default='')
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xizmat So'rovi"
        verbose_name_plural = "Xizmat So'rovlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"So'rov #{self.id} ({self.status})"

    def can_transition_to(self, new_status):
        return new_status in self.STATUS_FLOW.get(self.status, [])


class Review(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest, on_delete=models.CASCADE, related_name='review'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"Sharh #{self.id}: {self.rating}⭐"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.provider.provider_profile.update_rating()
        except Exception:
            pass
