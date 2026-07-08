from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["user"]


    # ==========================================
    # PHONE VALIDATION
    # ==========================================

    def validate_phone(self, value):

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return value

        value = value.strip()

        queryset = Customer.objects.filter(
            user=request.user,
            phone=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A customer with this phone number already exists."
            )

        return value


    # ==========================================
    # EMAIL VALIDATION
    # ==========================================

    def validate_email(self, value):

        if not value:
            return None

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return value

        value = value.strip().lower()

        queryset = Customer.objects.filter(
            user=request.user,
            email__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A customer with this email already exists."
            )

        return value