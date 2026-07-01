from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

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

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        return user


# ----------------------------
# Forgot Password
# ----------------------------

class ForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()

    new_password = serializers.CharField(min_length=6)