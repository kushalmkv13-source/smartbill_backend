from django.db import models
from django.contrib.auth.models import User


class PasswordResetOTP(models.Model):

    email = models.EmailField()

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email


# ==========================================
# USER LOGIN SESSION TRACKING
# ==========================================

class UserSession(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="login_session"
    )

    is_online = models.BooleanField(default=False)

    login_time = models.DateTimeField(
        null=True,
        blank=True
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True
    )

    logout_time = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"