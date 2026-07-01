from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "phone"],
                name="unique_phone_per_user"
            ),
            models.UniqueConstraint(
                fields=["user", "email"],
                name="unique_email_per_user"
            ),
        ]

    def __str__(self):
        return self.full_name