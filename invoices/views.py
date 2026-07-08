from decimal import Decimal

from django.db import transaction

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from rest_framework_simplejwt.authentication import (
    JWTAuthentication,
)

from authentication.audit import create_audit_log

from products.models import Product

from .models import Invoice, InvoiceItem
from .serializers import (
    InvoiceSerializer,
    InvoiceItemSerializer,
)


# =====================================================
# INVOICE VIEWSET
# =====================================================

class InvoiceViewSet(viewsets.ModelViewSet):

    serializer_class = InvoiceSerializer

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        return (
            Invoice.objects
            .filter(user=self.request.user)
            .select_related("customer")
            .prefetch_related("items__product")
            .order_by("-id")
        )


    # =================================================
    # CREATE INVOICE
    # =================================================

    def perform_create(self, serializer):

        customer = serializer.validated_data[
            "customer"
        ]

        if customer.user_id != self.request.user.id:

            raise PermissionDenied(
                "You cannot use another user's customer."
            )


        invoice = serializer.save(
            user=self.request.user
        )


        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="INVOICE_CREATED",
            description=(
                f"Invoice '{invoice.invoice_number}' "
                f"was created."
            )
        )


    # =================================================
    # UPDATE INVOICE
    # =================================================

    def perform_update(self, serializer):

        customer = serializer.validated_data.get(
            "customer",
            serializer.instance.customer
        )


        if customer.user_id != self.request.user.id:

            raise PermissionDenied(
                "You cannot use another user's customer."
            )


        invoice = serializer.save(
            user=self.request.user
        )


        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="INVOICE_UPDATED",
            description=(
                f"Invoice '{invoice.invoice_number}' "
                f"was updated."
            )
        )


    # =================================================
    # DELETE INVOICE
    # RESTORE PRODUCT STOCK
    # =================================================

    @transaction.atomic
    def perform_destroy(self, instance):

        invoice_number = instance.invoice_number


        items = (
            instance.items
            .select_related("product")
            .order_by("product_id")
        )


        for item in items:

            product = (
                Product.objects
                .select_for_update()
                .get(
                    pk=item.product_id,
                    user=self.request.user
                )
            )


            product.stock += item.quantity


            product.save(
                update_fields=["stock"]
            )


        instance.delete()


        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="INVOICE_DELETED",
            description=(
                f"Invoice '{invoice_number}' "
                f"was deleted."
            )
        )


# =====================================================
# INVOICE ITEM VIEWSET
# =====================================================

class InvoiceItemViewSet(viewsets.ModelViewSet):

    serializer_class = InvoiceItemSerializer

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        return (
            InvoiceItem.objects
            .filter(
                invoice__user=self.request.user
            )
            .select_related(
                "invoice",
                "product"
            )
            .order_by("-id")
        )


    # =================================================
    # CREATE INVOICE ITEM
    # =================================================

    @transaction.atomic
    def perform_create(self, serializer):

        invoice = serializer.validated_data[
            "invoice"
        ]


        submitted_product = (
            serializer.validated_data[
                "product"
            ]
        )


        quantity = serializer.validated_data[
            "quantity"
        ]


        # ---------------------------------------------
        # INVOICE OWNERSHIP CHECK
        # ---------------------------------------------

        if invoice.user_id != self.request.user.id:

            raise PermissionDenied(
                "You cannot add items to this invoice."
            )


        # ---------------------------------------------
        # PRODUCT OWNERSHIP CHECK
        # ---------------------------------------------

        if (
            submitted_product.user_id
            != self.request.user.id
        ):

            raise PermissionDenied(
                "You cannot use this product."
            )


        # ---------------------------------------------
        # QUANTITY VALIDATION
        # ---------------------------------------------

        if quantity <= 0:

            raise ValidationError({
                "quantity":
                    "Quantity must be greater than zero."
            })


        # ---------------------------------------------
        # LOCK PRODUCT ROW
        # ---------------------------------------------

        product = (
            Product.objects
            .select_for_update()
            .get(
                pk=submitted_product.pk,
                user=self.request.user
            )
        )


        # ---------------------------------------------
        # STOCK VALIDATION
        # ---------------------------------------------

        if product.stock < quantity:

            raise ValidationError({
                "quantity": (
                    f"Only {product.stock} "
                    f"items available."
                )
            })


        # ---------------------------------------------
        # BACKEND PRICE CALCULATION
        # ---------------------------------------------

        price = product.price

        gst = product.gst


        base_total = (
            price * Decimal(quantity)
        )


        gst_amount = (
            base_total
            * gst
            / Decimal("100")
        )


        total = (
            base_total + gst_amount
        )


        # ---------------------------------------------
        # DEDUCT STOCK
        # ---------------------------------------------

        product.stock -= quantity


        product.save(
            update_fields=["stock"]
        )


        # ---------------------------------------------
        # SAVE SECURE VALUES
        # ---------------------------------------------

        serializer.save(
            product=product,
            price=price,
            gst=gst,
            total=total
        )


    # =================================================
    # UPDATE INVOICE ITEM
    # =================================================

    @transaction.atomic
    def perform_update(self, serializer):

        old_item = self.get_object()


        old_product_id = (
            old_item.product_id
        )


        old_quantity = (
            old_item.quantity
        )


        new_invoice = serializer.validated_data.get(
            "invoice",
            old_item.invoice
        )


        submitted_new_product = (
            serializer.validated_data.get(
                "product",
                old_item.product
            )
        )


        new_quantity = (
            serializer.validated_data.get(
                "quantity",
                old_quantity
            )
        )


        # ---------------------------------------------
        # OWNERSHIP CHECKS
        # ---------------------------------------------

        if (
            new_invoice.user_id
            != self.request.user.id
        ):

            raise PermissionDenied(
                "You cannot use this invoice."
            )


        if (
            submitted_new_product.user_id
            != self.request.user.id
        ):

            raise PermissionDenied(
                "You cannot use this product."
            )


        if new_quantity <= 0:

            raise ValidationError({
                "quantity":
                    "Quantity must be greater than zero."
            })


        # =================================================
        # SAME PRODUCT
        # =================================================

        if (
            submitted_new_product.pk
            == old_product_id
        ):

            product = (
                Product.objects
                .select_for_update()
                .get(
                    pk=old_product_id,
                    user=self.request.user
                )
            )


            available_stock = (
                product.stock
                + old_quantity
            )


            if available_stock < new_quantity:

                raise ValidationError({
                    "quantity": (
                        f"Only {available_stock} "
                        f"items available."
                    )
                })


            # -----------------------------------------
            # RECALCULATE FINANCIAL VALUES
            # -----------------------------------------

            price = product.price

            gst = product.gst


            base_total = (
                price
                * Decimal(new_quantity)
            )


            gst_amount = (
                base_total
                * gst
                / Decimal("100")
            )


            total = (
                base_total
                + gst_amount
            )


            # -----------------------------------------
            # UPDATE STOCK
            # -----------------------------------------

            product.stock = (
                available_stock
                - new_quantity
            )


            product.save(
                update_fields=["stock"]
            )


            # -----------------------------------------
            # SAVE ITEM
            # -----------------------------------------

            serializer.save(
                product=product,
                price=price,
                gst=gst,
                total=total
            )


        # =================================================
        # PRODUCT CHANGED
        # =================================================

        else:

            product_ids = sorted([
                old_product_id,
                submitted_new_product.pk
            ])


            locked_products = {

                product.pk: product

                for product in (

                    Product.objects
                    .select_for_update()
                    .filter(
                        pk__in=product_ids
                    )
                    .order_by("pk")

                )
            }


            old_product = locked_products.get(
                old_product_id
            )


            new_product = locked_products.get(
                submitted_new_product.pk
            )


            if (
                not old_product
                or not new_product
            ):

                raise ValidationError(
                    "Product not found."
                )


            if (
                old_product.user_id
                != self.request.user.id
            ):

                raise PermissionDenied(
                    "You cannot use this product."
                )


            if (
                new_product.user_id
                != self.request.user.id
            ):

                raise PermissionDenied(
                    "You cannot use this product."
                )


            # -----------------------------------------
            # CHECK NEW PRODUCT STOCK
            # -----------------------------------------

            if (
                new_product.stock
                < new_quantity
            ):

                raise ValidationError({
                    "quantity": (
                        f"Only {new_product.stock} "
                        f"items available."
                    )
                })


            # -----------------------------------------
            # RESTORE OLD PRODUCT STOCK
            # -----------------------------------------

            old_product.stock += (
                old_quantity
            )


            # -----------------------------------------
            # DEDUCT NEW PRODUCT STOCK
            # -----------------------------------------

            new_product.stock -= (
                new_quantity
            )


            old_product.save(
                update_fields=["stock"]
            )


            new_product.save(
                update_fields=["stock"]
            )


            # -----------------------------------------
            # CALCULATE USING NEW PRODUCT VALUES
            # -----------------------------------------

            price = new_product.price

            gst = new_product.gst


            base_total = (
                price
                * Decimal(new_quantity)
            )


            gst_amount = (
                base_total
                * gst
                / Decimal("100")
            )


            total = (
                base_total
                + gst_amount
            )


            # -----------------------------------------
            # SAVE UPDATED ITEM
            # -----------------------------------------

            serializer.save(
                product=new_product,
                price=price,
                gst=gst,
                total=total
            )


    # =================================================
    # DELETE INVOICE ITEM
    # RESTORE STOCK
    # =================================================

    @transaction.atomic
    def perform_destroy(self, instance):

        product = (
            Product.objects
            .select_for_update()
            .get(
                pk=instance.product_id,
                user=self.request.user
            )
        )


        product.stock += (
            instance.quantity
        )


        product.save(
            update_fields=["stock"]
        )


        instance.delete()