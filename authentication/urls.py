from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    AdminUsersView,
    AuditLogListView,
)


urlpatterns = [

    # =================================================
    # AUTHENTICATION
    # =================================================

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout"
    ),


    # =================================================
    # PASSWORD RESET
    # =================================================

    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot-password"
    ),

    path(
        "verify-otp/",
        VerifyOTPView.as_view(),
        name="verify-otp"
    ),

    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password"
    ),


    # =================================================
    # ADMIN USER MANAGEMENT
    # =================================================

    path(
        "admin/users/",
        AdminUsersView.as_view(),
        name="admin-users"
    ),

    path(
        "admin/users/<int:user_id>/",
        AdminUsersView.as_view(),
        name="admin-user-detail"
    ),


    # =================================================
    # ADMIN AUDIT LOGS
    # =================================================

    path(
        "audit-logs/",
        AuditLogListView.as_view(),
        name="audit-logs"
    ),
]