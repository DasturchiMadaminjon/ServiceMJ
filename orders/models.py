from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from services.models import Category


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

    CURRENCY_CHOICES = (
        ('UZS', "so'm"),
        ('USD', 'USD'),
    )

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
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')
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
            # Usta reytingini yangilash
            self.provider.provider_profile.update_rating()
        except Exception:
            pass
