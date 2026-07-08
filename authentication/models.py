from django.db import models
from django.contrib.auth.models import User


# =====================================================
# PASSWORD RESET OTP
# =====================================================

class PasswordResetOTP(models.Model):

    email = models.EmailField(
        unique=True
    )

    otp = models.CharField(
        max_length=6
    )

    reset_token = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    failed_attempts = models.PositiveSmallIntegerField(
        default=0
    )

    def __str__(self):
        return self.email


# =====================================================
# USER LOGIN SESSION TRACKING
# =====================================================

class UserSession(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="login_session"
    )

    is_online = models.BooleanField(
        default=False
    )

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

        status = (
            "Online"
            if self.is_online
            else "Offline"
        )

        return (
            f"{self.user.username} - {status}"
        )
    # =====================================================
# AUDIT LOG
# =====================================================

class AuditLog(models.Model):

    ACTION_CHOICES = [

        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAILED", "Login Failed"),
        ("LOGOUT", "Logout"),

        (
            "PASSWORD_RESET_REQUEST",
            "Password Reset Request"
        ),

        (
            "PASSWORD_RESET_SUCCESS",
            "Password Reset Success"
        ),

        ("CUSTOMER_CREATED", "Customer Created"),
        ("CUSTOMER_UPDATED", "Customer Updated"),
        ("CUSTOMER_DELETED", "Customer Deleted"),

        ("PRODUCT_CREATED", "Product Created"),
        ("PRODUCT_UPDATED", "Product Updated"),
        ("PRODUCT_DELETED", "Product Deleted"),

        ("INVOICE_CREATED", "Invoice Created"),
        ("INVOICE_UPDATED", "Invoice Updated"),
        ("INVOICE_DELETED", "Invoice Deleted"),
    ]


    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )


    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )


    description = models.TextField(
        blank=True,
        default=""
    )


    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )


    user_agent = models.TextField(
        blank=True,
        default=""
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        ordering = [
            "-created_at"
        ]

        indexes = [

            models.Index(
                fields=[
                    "user",
                    "created_at"
                ]
            ),

            models.Index(
                fields=[
                    "action",
                    "created_at"
                ]
            ),
        ]


    def __str__(self):

        username = (
            self.user.username
            if self.user
            else "Anonymous"
        )

        return (
            f"{username} - "
            f"{self.action} - "
            f"{self.created_at}"
        )