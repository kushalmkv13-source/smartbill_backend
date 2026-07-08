from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Account


class AccountSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"}
    )

    class Meta:
        model = Account

        fields = [
            "id",
            "full_name",
            "business_name",
            "email",
            "phone",
            "password",
            "role",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


    # ==========================================
    # CREATE ACCOUNT
    # ==========================================

    def create(self, validated_data):

        password = validated_data.pop(
            "password",
            None
        )

        if not password:
            raise serializers.ValidationError({
                "password": "Password is required."
            })

        validated_data["password"] = make_password(
            password
        )

        return Account.objects.create(
            **validated_data
        )


    # ==========================================
    # UPDATE ACCOUNT
    # ==========================================

    def update(self, instance, validated_data):

        password = validated_data.pop(
            "password",
            None
        )

        for field, value in validated_data.items():
            setattr(
                instance,
                field,
                value
            )

        if password:
            instance.password = make_password(
                password
            )

        instance.save()

        return instance