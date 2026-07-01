import random
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetOTP
from .serializers import (
    RegisterSerializer,
    ForgotPasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class LoginView(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login Successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            })

        return Response(
            {"error": "Invalid username or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )


class ForgotPasswordView(APIView):

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        # filter().first() returns None, it does NOT raise DoesNotExist —
        # so we check for None directly instead of using try/except.
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": "Email not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete previous OTPs
        PasswordResetOTP.objects.filter(email=email).delete()

        # Generate new OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP
        PasswordResetOTP.objects.create(
            email=email,
            otp=otp
        )

        # Send Email
        send_mail(
            subject="InvoiceHub Password Reset OTP",
            message=f"Your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {"message": "OTP sent successfully."},
            status=status.HTTP_200_OK
        )


class VerifyOTPView(APIView):

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"error": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Same fix as above: filter().first() returns None, not DoesNotExist.
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp_obj = PasswordResetOTP.objects.get(
                email=email,
                otp=otp
            )
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP expires after 10 minutes
        if timezone.now() - otp_obj.created_at > timedelta(minutes=10):
            otp_obj.delete()
            return Response(
                {"error": "OTP has expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_obj.is_verified = True
        otp_obj.save()

        return Response(
            {"message": "OTP verified successfully."},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):

    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")

        if not email or not new_password:
            return Response(
                {"error": "Email and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp_obj = PasswordResetOTP.objects.get(
                email=email,
                is_verified=True
            )
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {"error": "OTP verification required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Re-check expiry: a verified-but-stale OTP shouldn't allow a reset
        # arbitrarily far in the future.
        if timezone.now() - otp_obj.created_at > timedelta(minutes=10):
            otp_obj.delete()
            return Response(
                {"error": "OTP has expired, please request a new one"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce Django's password validators (length, common password, etc.)
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        otp_obj.delete()

        return Response(
            {"message": "Password reset successfully."},
            status=status.HTTP_200_OK
        )