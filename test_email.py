import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject="InvoiceHub Test",
    message="Email configuration is working!",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["vardhanmkv13@gmail.com"],
    fail_silently=False,
)

print("✅ Email Sent Successfully")