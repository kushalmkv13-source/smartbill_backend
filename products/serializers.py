from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

        read_only_fields = [
            "user",
            "created_at",
        ]

    def validate_sku(self, value):

        request = self.context.get("request")

        if (
            not request
            or not request.user.is_authenticated
        ):
            return value

        value = value.strip()

        queryset = Product.objects.filter(
            user=request.user,
            sku__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists."
            )

        return value