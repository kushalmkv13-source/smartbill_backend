from rest_framework import serializers
from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.product_name",
        read_only=True
    )

    class Meta:
        model = InvoiceItem
        fields = "__all__"


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
        read_only_fields = ["user"]