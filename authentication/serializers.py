from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from .models import AuditLog


# =====================================================
# REGISTER SERIALIZER
# =====================================================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={
            "input_type": "password"
        }
    )


    class Meta:

        model = User

        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        ]

        read_only_fields = [
            "id"
        ]


    def validate_username(self, value):

        value = value.strip()

        if User.objects.filter(
            username=value
        ).exists():

            raise serializers.ValidationError(
                "Username already exists."
            )

        return value


    def validate_email(self, value):

        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "Email already exists."
            )

        return value


    def validate_password(self, value):

        validate_password(value)

        return value


    def create(self, validated_data):

        user = User.objects.create_user(

            username=validated_data[
                "username"
            ],

            email=validated_data[
                "email"
            ],

            password=validated_data[
                "password"
            ],

            first_name=validated_data.get(
                "first_name",
                ""
            ),

            last_name=validated_data.get(
                "last_name",
                ""
            )
        )

        return user


# =====================================================
# FORGOT PASSWORD SERIALIZER
# =====================================================

class ForgotPasswordSerializer(
    serializers.Serializer
):

    email = serializers.EmailField()


# =====================================================
# VERIFY OTP SERIALIZER
# =====================================================

class VerifyOTPSerializer(
    serializers.Serializer
):

    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )


# =====================================================
# RESET PASSWORD SERIALIZER
# =====================================================

class ResetPasswordSerializer(
    serializers.Serializer
):

    email = serializers.EmailField()

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={
            "input_type": "password"
        }
    )


    def validate_new_password(self, value):

        validate_password(value)

        return value


# =====================================================
# ADMIN USER SERIALIZER
# =====================================================

class AdminUserSerializer(
    serializers.ModelSerializer
):

    role = serializers.SerializerMethodField()


    class Meta:

        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
            "role",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
            "role",
        ]


    def get_role(self, obj):

        return (
            "admin"
            if obj.is_staff
            else "user"
        )


# =====================================================
# AUDIT LOG SERIALIZER
# =====================================================

class AuditLogSerializer(
    serializers.ModelSerializer
):

    username = serializers.SerializerMethodField()


    class Meta:

        model = AuditLog

        fields = [
            "id",
            "username",
            "action",
            "description",
            "ip_address",
            "user_agent",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "action",
            "description",
            "ip_address",
            "user_agent",
            "created_at",
        ]


    def get_username(self, obj):

        if obj.user:

            return obj.user.username

        return None