from django.db import models

class Account(models.Model):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )

    full_name = models.CharField(max_length=100)
    business_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=255)

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name