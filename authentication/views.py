import secrets
from datetime import timedelta
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import (
    validate_password,
)
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
)
from rest_framework.throttling import ScopedRateThrottle

from rest_framework_simplejwt.authentication import (
    JWTAuthentication,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    PasswordResetOTP,
    UserSession,
    AuditLog,
)

from .audit import create_audit_log

from .serializers import (
    RegisterSerializer,
    ForgotPasswordSerializer,
    AdminUserSerializer,
    AuditLogSerializer,
)


# =====================================================
# REGISTER
# =====================================================

class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer


# =====================================================
# LOGIN
# =====================================================

class LoginView(APIView):

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "login"


    def post(self, request):

        username = request.data.get(
            "username"
        )

        password = request.data.get(
            "password"
        )


        # ---------------------------------------------
        # CHECK REQUIRED FIELDS
        # ---------------------------------------------

        if not username or not password:

            return Response(
                {
                    "success": False,
                    "message":
                        "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # AUTHENTICATE USER
        # ---------------------------------------------

        user = authenticate(
            username=username,
            password=password
        )


        # ---------------------------------------------
        # FAILED LOGIN
        # ---------------------------------------------

        if not user:

            create_audit_log(
                request=request,
                action="LOGIN_FAILED",
                description=(
                    f"Failed login attempt for username: "
                    f"{username}"
                )
            )


            return Response(
                {
                    "success": False,
                    "message":
                        "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


        # ---------------------------------------------
        # CREATE JWT TOKENS
        # ---------------------------------------------

        refresh = RefreshToken.for_user(
            user
        )


        # ---------------------------------------------
        # UPDATE USER SESSION
        # ---------------------------------------------

        user_session, created = (
            UserSession.objects.get_or_create(
                user=user
            )
        )


        user_session.is_online = True

        user_session.login_time = (
            timezone.now()
        )

        user_session.last_seen = (
            timezone.now()
        )

        user_session.logout_time = None

        user_session.save()


        # ---------------------------------------------
        # AUDIT SUCCESSFUL LOGIN
        # ---------------------------------------------

        create_audit_log(
            request=request,
            user=user,
            action="LOGIN_SUCCESS",
            description=(
                "User logged in successfully."
            )
        )


        # ---------------------------------------------
        # LOGIN RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "success": True,

                "message":
                    "Login Successful",

                "access":
                    str(refresh.access_token),

                "refresh":
                    str(refresh),

                "user": {

                    "id":
                        user.id,

                    "username":
                        user.username,

                    "email":
                        user.email,

                    "first_name":
                        user.first_name,

                    "last_name":
                        user.last_name,

                    "is_staff":
                        user.is_staff,

                    "is_superuser":
                        user.is_superuser,

                    "role":
                        (
                            "admin"
                            if user.is_staff
                            else "user"
                        )
                }
            },
            status=status.HTTP_200_OK
        )


# =====================================================
# LOGOUT
# =====================================================

class LogoutView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    def post(self, request):

        refresh_token = request.data.get(
            "refresh"
        )


        if not refresh_token:

            return Response(
                {
                    "success": False,
                    "message":
                        "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        try:

            token = RefreshToken(
                refresh_token
            )

            token.blacklist()


            UserSession.objects.filter(
                user=request.user
            ).update(

                is_online=False,

                last_seen=timezone.now(),

                logout_time=timezone.now()
            )


            create_audit_log(
                request=request,
                user=request.user,
                action="LOGOUT",
                description=(
                    "User logged out successfully."
                )
            )


            return Response(
                {
                    "success": True,
                    "message":
                        "Logged out successfully."
                },
                status=status.HTTP_200_OK
            )


        except Exception:

            return Response(
                {
                    "success": False,
                    "message":
                        "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# =====================================================
# FORGOT PASSWORD
# =====================================================

class ForgotPasswordView(APIView):

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "forgot_password"


    def post(self, request):

        serializer = ForgotPasswordSerializer(
            data=request.data
        )


        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        email = (
            serializer
            .validated_data["email"]
            .strip()
            .lower()
        )


        user = User.objects.filter(
            email__iexact=email
        ).first()


        # Prevent email enumeration
        if not user:

            return Response(
                {
                    "success": True,

                    "message":
                        "If an account exists with this email, "
                        "an OTP has been sent."
                },
                status=status.HTTP_200_OK
            )


        # Remove previous OTP/reset session
        PasswordResetOTP.objects.filter(
            email=email
        ).delete()


        otp = str(
            secrets.randbelow(900000)
            + 100000
        )


        PasswordResetOTP.objects.create(

            email=email,

            otp=otp,

            is_verified=False,

            failed_attempts=0,

            reset_token=None
        )


        send_mail(

            subject=
                "InvoiceHub Password Reset OTP",

            message=
                f"Your password reset OTP is: {otp}\n\n"
                "This OTP expires in 10 minutes.",

            from_email=
                settings.DEFAULT_FROM_EMAIL,

            recipient_list=[
                email
            ],

            fail_silently=False
        )


        create_audit_log(
            request=request,
            user=user,
            action="PASSWORD_RESET_REQUEST",
            description=(
                "Password reset OTP requested."
            )
        )


        return Response(
            {
                "success": True,

                "message":
                    "If an account exists with this email, "
                    "an OTP has been sent."
            },
            status=status.HTTP_200_OK
        )


# =====================================================
# VERIFY OTP
# =====================================================

class VerifyOTPView(APIView):

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "verify_otp"

    MAX_ATTEMPTS = 5

    OTP_EXPIRY_MINUTES = 10


    def post(self, request):

        email = request.data.get(
            "email"
        )

        otp = request.data.get(
            "otp"
        )


        if not email or not otp:

            return Response(
                {
                    "success": False,

                    "message":
                        "Email and OTP are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        email = email.strip().lower()

        otp = str(otp).strip()


        try:

            otp_obj = (
                PasswordResetOTP.objects.get(
                    email=email
                )
            )


        except PasswordResetOTP.DoesNotExist:

            return Response(
                {
                    "success": False,

                    "message":
                        "Invalid or expired OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # CHECK OTP EXPIRY
        # ---------------------------------------------

        if (
            timezone.now()
            - otp_obj.created_at
            >
            timedelta(
                minutes=self.OTP_EXPIRY_MINUTES
            )
        ):

            otp_obj.delete()


            return Response(
                {
                    "success": False,

                    "message":
                        "Invalid or expired OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # BLOCK TOO MANY ATTEMPTS
        # ---------------------------------------------

        if (
            otp_obj.failed_attempts
            >= self.MAX_ATTEMPTS
        ):

            otp_obj.delete()


            return Response(
                {
                    "success": False,

                    "message":
                        "Too many failed attempts. "
                        "Request a new OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # SECURE OTP COMPARISON
        # ---------------------------------------------

        if not secrets.compare_digest(
            str(otp_obj.otp),
            otp
        ):

            otp_obj.failed_attempts += 1


            remaining_attempts = (
                self.MAX_ATTEMPTS
                - otp_obj.failed_attempts
            )


            otp_obj.save(
                update_fields=[
                    "failed_attempts"
                ]
            )


            if remaining_attempts <= 0:

                otp_obj.delete()


                return Response(
                    {
                        "success": False,

                        "message":
                            "Too many failed attempts. "
                            "Request a new OTP."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            return Response(
                {
                    "success": False,

                    "message":
                        "Invalid OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # GENERATE SECURE RESET TOKEN
        # ---------------------------------------------

        reset_token = secrets.token_urlsafe(
            48
        )


        otp_obj.is_verified = True

        otp_obj.reset_token = reset_token


        otp_obj.save(
            update_fields=[
                "is_verified",
                "reset_token"
            ]
        )


        return Response(
            {
                "success": True,

                "message":
                    "OTP verified successfully.",

                "reset_token":
                    reset_token
            },
            status=status.HTTP_200_OK
        )


# =====================================================
# RESET PASSWORD
# =====================================================

class ResetPasswordView(APIView):

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "reset_password"

    RESET_EXPIRY_MINUTES = 10


    def post(self, request):

        email = request.data.get(
            "email"
        )

        reset_token = request.data.get(
            "reset_token"
        )

        new_password = request.data.get(
            "new_password"
        )


        if (
            not email
            or not reset_token
            or not new_password
        ):

            return Response(
                {
                    "success": False,

                    "message":
                        "Email, reset token and "
                        "new password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        email = email.strip().lower()

        reset_token = reset_token.strip()


        try:

            user = User.objects.get(
                email__iexact=email
            )


        except User.DoesNotExist:

            return Response(
                {
                    "success": False,

                    "message":
                        "Unable to reset password."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        try:

            otp_obj = (
                PasswordResetOTP.objects.get(
                    email=email,
                    is_verified=True
                )
            )


        except PasswordResetOTP.DoesNotExist:

            return Response(
                {
                    "success": False,

                    "message":
                        "OTP verification required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # CHECK RESET SESSION EXPIRY
        # ---------------------------------------------

        if (
            timezone.now()
            - otp_obj.created_at
            >
            timedelta(
                minutes=self.RESET_EXPIRY_MINUTES
            )
        ):

            otp_obj.delete()


            return Response(
                {
                    "success": False,

                    "message":
                        "Reset session expired. "
                        "Please request a new OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ---------------------------------------------
        # SECURE TOKEN COMPARISON
        # ---------------------------------------------

        stored_token = (
            otp_obj.reset_token or ""
        )


        if not secrets.compare_digest(
            stored_token,
            reset_token
        ):

            return Response(
                {
                    "success": False,

                    "message":
                        "Invalid reset authorization."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        try:

            validate_password(
                new_password,
                user=user
            )


        except ValidationError as error:

            return Response(
                {
                    "success": False,

                    "message":
                        error.messages
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        user.set_password(
            new_password
        )


        user.save(
            update_fields=[
                "password"
            ]
        )


        # Destroy reset authorization
        otp_obj.delete()


        # Mark tracked session offline
        UserSession.objects.filter(
            user=user
        ).update(

            is_online=False,

            last_seen=timezone.now(),

            logout_time=timezone.now()
        )


        create_audit_log(
            request=request,
            user=user,
            action="PASSWORD_RESET_SUCCESS",
            description=(
                "Password reset completed successfully."
            )
        )


        return Response(
            {
                "success": True,

                "message":
                    "Password reset successfully."
            },
            status=status.HTTP_200_OK
        )


# =====================================================
# ADMIN USERS
# =====================================================

class AdminUsersView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    # =================================================
    # GET USERS
    # =================================================

    def get(self, request):

        if not request.user.is_staff:

            return Response(
                {
                    "error":
                        "Access Denied"
                },
                status=status.HTTP_403_FORBIDDEN
            )


        users = User.objects.all().order_by(
            "-date_joined"
        )


        serializer = AdminUserSerializer(
            users,
            many=True
        )


        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # =================================================
    # UPDATE USER
    # =================================================

    def patch(
        self,
        request,
        user_id
    ):

        if not request.user.is_staff:

            return Response(
                {
                    "error":
                        "Access Denied"
                },
                status=status.HTTP_403_FORBIDDEN
            )


        try:

            user = User.objects.get(
                id=user_id
            )


        except User.DoesNotExist:

            return Response(
                {
                    "error":
                        "User not found"
                },
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

            is_active = request.data[
                "is_active"
            ]

            if not isinstance(
                is_active,
                bool
            ):

                return Response(
                    {
                        "success": False,

                        "message":
                            "is_active must be true or false."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            user.is_active = is_active


        user.save()


        serializer = AdminUserSerializer(
            user
        )


        return Response(
            {
                "success": True,

                "message":
                    "User updated successfully",

                "user":
                    serializer.data
            },
            status=status.HTTP_200_OK
        )


    # =================================================
    # DELETE USER
    # =================================================

    def delete(
        self,
        request,
        user_id
    ):

        if not request.user.is_staff:

            return Response(
                {
                    "success": False,

                    "message":
                        "Access Denied"
                },
                status=status.HTTP_403_FORBIDDEN
            )


        try:

            user = User.objects.get(
                id=user_id
            )


        except User.DoesNotExist:

            return Response(
                {
                    "success": False,

                    "message":
                        "User not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )


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


        user.delete()


        return Response(
            {
                "success": True,

                "message":
                    f"User {username} deleted successfully"
            },
            status=status.HTTP_200_OK
        )

# =====================================================
# ADMIN AUDIT LOGS
# =====================================================
class AuditLogPagination(PageNumberPagination):

    page_size = 20

    page_size_query_param = "page_size"

    max_page_size = 100

class AuditLogListView(ListAPIView):

    serializer_class = AuditLogSerializer

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAdminUser
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "user__username",
        "user__email",
        "action",
        "description",
        "ip_address",
    ]

    ordering_fields = [
        "created_at",
        "action",
    ]

    ordering = [
        "-created_at"
    ]


    def get_queryset(self):

        queryset = (
            AuditLog.objects
            .select_related("user")
            .order_by("-created_at")
        )


        # ---------------------------------------------
        # FILTER BY ACTION
        # ---------------------------------------------

        action = self.request.query_params.get(
            "action"
        )

        if action:

            queryset = queryset.filter(
                action__iexact=action
            )


        # ---------------------------------------------
        # FILTER BY USERNAME
        # ---------------------------------------------

        username = self.request.query_params.get(
            "username"
        )

        if username:

            queryset = queryset.filter(
                user__username__icontains=username
            )


        # ---------------------------------------------
        # FILTER BY START DATE
        # ---------------------------------------------

        start_date = self.request.query_params.get(
            "start_date"
        )

        if start_date:

            queryset = queryset.filter(
                created_at__date__gte=start_date
            )


        # ---------------------------------------------
        # FILTER BY END DATE
        # ---------------------------------------------

        end_date = self.request.query_params.get(
            "end_date"
        )

        if end_date:

            queryset = queryset.filter(
                created_at__date__lte=end_date
            )


        return queryset