from django.db import transaction

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceItemSerializer


class InvoiceViewSet(viewsets.ModelViewSet):

    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(
            user=self.request.user
        ).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):

        for item in instance.items.all():

            product = item.product

            product.stock += item.quantity

            product.save()

        instance.delete()


class InvoiceItemViewSet(viewsets.ModelViewSet):

    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InvoiceItem.objects.filter(
            invoice__user=self.request.user
        )

    @transaction.atomic
    def perform_create(self, serializer):

        invoice = serializer.validated_data["invoice"]
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        if invoice.user != self.request.user:
            raise PermissionDenied("Invalid Invoice.")

        if product.stock < quantity:
            raise PermissionDenied(
                f"Only {product.stock} items available."
            )

        product.stock -= quantity
        product.save()

        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):

        old_item = self.get_object()

        old_qty = old_item.quantity
        product = old_item.product
        new_qty = serializer.validated_data["quantity"]

        available_stock = product.stock + old_qty

        if available_stock < new_qty:
            raise PermissionDenied(
                f"Only {available_stock} items available."
            )

        product.stock = available_stock - new_qty
        product.save()

        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):

        product = instance.product

        product.stock += instance.quantity

        product.save()

        instance.delete()