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
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetOTP, UserSession
from .serializers import (
    RegisterSerializer,
    ForgotPasswordSerializer,
    AdminUserSerializer,
)


# ==========================================
# REGISTER
# ==========================================

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

# ==========================================
# LOGIN
# ==========================================

class LoginView(APIView):

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        # Check empty fields
        if not username or not password:
            return Response(
                {
                    "success": False,
                    "message": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(
            username=username,
            password=password
        )

        # ==========================================
        # LOGIN SUCCESS
        # ==========================================

        if user:

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Create or get login session
            user_session, created = UserSession.objects.get_or_create(
                user=user
            )

            # Mark user as online
            user_session.is_online = True
            user_session.login_time = timezone.now()
            user_session.last_seen = timezone.now()
            user_session.logout_time = None
            user_session.save()

            # Return login response
            return Response(
                {
                    "success": True,
                    "message": "Login Successful",

                    "access": str(refresh.access_token),
                    "refresh": str(refresh),

                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "role": "admin" if user.is_staff else "user"
                    }
                },
                status=status.HTTP_200_OK
            )

        # ==========================================
        # LOGIN FAILED
        # ==========================================

        return Response(
            {
                "success": False,
                "message": "Invalid username or password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

# ==========================================
# FORGOT PASSWORD
# ==========================================

class ForgotPasswordView(APIView):

    def post(self, request):

        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {
                    "success": False,
                    "message": "Email not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        PasswordResetOTP.objects.filter(email=email).delete()

        otp = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(
            email=email,
            otp=otp
        )

        send_mail(
            subject="InvoiceHub Password Reset OTP",
            message=f"Your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "success": True,
                "message": "OTP sent successfully."
            },
            status=status.HTTP_200_OK
        )


# ==========================================
# VERIFY OTP
# ==========================================

class VerifyOTPView(APIView):

    def post(self, request):

        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {
                    "success": False,
                    "message": "Email and OTP are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {
                    "success": False,
                    "message": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp_obj = PasswordResetOTP.objects.get(
                email=email,
                otp=otp
            )
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Invalid OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() - otp_obj.created_at > timedelta(minutes=10):
            otp_obj.delete()

            return Response(
                {
                    "success": False,
                    "message": "OTP has expired."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_obj.is_verified = True
        otp_obj.save()

        return Response(
            {
                "success": True,
                "message": "OTP verified successfully."
            },
            status=status.HTTP_200_OK
        )


# ==========================================
# RESET PASSWORD
# ==========================================

class ResetPasswordView(APIView):

    def post(self, request):

        email = request.data.get("email")
        new_password = request.data.get("new_password")

        if not email or not new_password:
            return Response(
                {
                    "success": False,
                    "message": "Email and new password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp_obj = PasswordResetOTP.objects.get(
                email=email,
                is_verified=True
            )

        except PasswordResetOTP.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "OTP verification required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() - otp_obj.created_at > timedelta(minutes=10):
            otp_obj.delete()

            return Response(
                {
                    "success": False,
                    "message": "OTP expired. Please request a new OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user=user)

        except ValidationError as e:

            return Response(
                {
                    "success": False,
                    "message": e.messages
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        otp_obj.delete()

        return Response(
            {
                "success": True,
                "message": "Password reset successfully."
            },
            status=status.HTTP_200_OK
        )
    # ==========================================
# ADMIN USERS
# ==========================================
class AdminUsersView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


    # ==========================================
    # GET ALL USERS
    # ==========================================

    def get(self, request):

        if not request.user.is_staff:
            return Response(
                {"error": "Access Denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.all().order_by("-date_joined")

        serializer = AdminUserSerializer(
            users,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # ==========================================
    # UPDATE USER
    # ==========================================

    def patch(self, request, user_id):

        if not request.user.is_staff:
            return Response(
                {"error": "Access Denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


        user.first_name = request.data.get(
            "first_name",
            user.first_name
        )

        user.last_name = request.data.get(
            "last_name",
            user.last_name
        )

        user.email = request.data.get(
            "email",
            user.email
        )


        if "is_active" in request.data:

            user.is_active = request.data["is_active"]


        user.save()


        serializer = AdminUserSerializer(user)


        return Response(
            {
                "success": True,
                "message": "User updated successfully",
                "user": serializer.data
            },
            status=status.HTTP_200_OK
        )


    # ==========================================
    # DELETE USER
    # ==========================================

    def delete(self, request, user_id):

        # Admin permission check
        if not request.user.is_staff:

            return Response(
                {
                    "success": False,
                    "message": "Access Denied"
                },
                status=status.HTTP_403_FORBIDDEN
            )


        # Find user
        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )


        # Prevent currently logged-in admin
        # from deleting their own account

        if user.id == request.user.id:

            return Response(
                {
                    "success": False,
                    "message":
                    "You cannot delete your own admin account."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        username = user.username


        # Delete from database
        user.delete()


        return Response(
            {
                "success": True,
                "message":
                f"User {username} deleted successfully"
            },
            status=status.HTTP_200_OK
        )