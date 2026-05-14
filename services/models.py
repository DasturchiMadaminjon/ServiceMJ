from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ProviderProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_profile')
    bio = models.TextField()
    experience_years = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, related_name='providers', blank=True)

    def __str__(self):
        return f"Usta: {self.user.username}"

class Portfolio(models.Model):
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='portfolio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Tugallandi'),
        ('cancelled', 'Bekor qilindi'),
    )
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_requests')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"So'rov #{self.id} - {self.category}"

class Review(models.Model):
    request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.provider} - {self.rating} stars"
