from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    AdminUsersView,
)
urlpatterns = [

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
]