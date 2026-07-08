from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from authentication.audit import create_audit_log

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):

    serializer_class = ProductSerializer

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    # =================================================
    # USER-SPECIFIC PRODUCTS
    # =================================================

    def get_queryset(self):

        return (
            Product.objects
            .filter(user=self.request.user)
            .order_by("-id")
        )


    # =================================================
    # CREATE PRODUCT
    # =================================================

    def perform_create(self, serializer):

        product = serializer.save(
            user=self.request.user
        )

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="PRODUCT_CREATED",
            description=(
                f"Product '{product.product_name}' "
                f"was created."
            )
        )


    # =================================================
    # UPDATE PRODUCT
    # =================================================

    def perform_update(self, serializer):

        product = serializer.save(
            user=self.request.user
        )

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="PRODUCT_UPDATED",
            description=(
                f"Product '{product.product_name}' "
                f"was updated."
            )
        )


    # =================================================
    # DELETE PRODUCT
    # =================================================

    def perform_destroy(self, instance):

        product_name = instance.product_name

        instance.delete()

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="PRODUCT_DELETED",
            description=(
                f"Product '{product_name}' "
                f"was deleted."
            )
        )