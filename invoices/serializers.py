from rest_framework import serializers

from .models import Invoice, InvoiceItem


# =====================================================
# INVOICE ITEM SERIALIZER
# =====================================================

class InvoiceItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.product_name",
        read_only=True
    )

    class Meta:
        model = InvoiceItem
        fields = "__all__"


    def validate(self, attrs):

        request = self.context.get("request")

        if (
            not request
            or not request.user.is_authenticated
        ):
            return attrs


        # Existing values are used during PATCH
        invoice = attrs.get(
            "invoice",
            getattr(self.instance, "invoice", None)
        )

        product = attrs.get(
            "product",
            getattr(self.instance, "product", None)
        )


        # Validate invoice ownership
        if (
            invoice
            and invoice.user_id != request.user.id
        ):
            raise serializers.ValidationError({
                "invoice":
                    "You cannot use another user's invoice."
            })


        # Validate product ownership
        if (
            product
            and product.user_id != request.user.id
        ):
            raise serializers.ValidationError({
                "product":
                    "You cannot use another user's product."
            })


        return attrs


# =====================================================
# INVOICE SERIALIZER
# =====================================================

class InvoiceSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    items = InvoiceItemSerializer(
        many=True,
        read_only=True
    )


    class Meta:
        model = Invoice
        fields = "__all__"

        read_only_fields = [
            "user",
            "created_at",
        ]


    def validate_customer(self, customer):

        request = self.context.get("request")

        if (
            request
            and request.user.is_authenticated
            and customer.user_id != request.user.id
        ):
            raise serializers.ValidationError(
                "You cannot create an invoice for another user's customer."
            )

        return customer