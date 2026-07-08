from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Customer
from .serializers import CustomerSerializer

from authentication.audit import create_audit_log


class CustomerViewSet(viewsets.ModelViewSet):

    serializer_class = CustomerSerializer

    authentication_classes = [
        JWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        return (
            Customer.objects
            .filter(user=self.request.user)
            .order_by("-id")
        )


    # =================================================
    # CREATE CUSTOMER
    # =================================================

    def perform_create(self, serializer):

        customer = serializer.save(
            user=self.request.user
        )

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="CUSTOMER_CREATED",
            description=(
                f"Customer '{customer.full_name}' "
                f"was created."
            )
        )


    # =================================================
    # UPDATE CUSTOMER
    # =================================================

    def perform_update(self, serializer):

        customer = serializer.save(
            user=self.request.user
        )

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="CUSTOMER_UPDATED",
            description=(
                f"Customer '{customer.full_name}' "
                f"was updated."
            )
        )


    # =================================================
    # DELETE CUSTOMER
    # =================================================

    def perform_destroy(self, instance):

        customer_name = instance.full_name

        instance.delete()

        create_audit_log(
            request=self.request,
            user=self.request.user,
            action="CUSTOMER_DELETED",
            description=(
                f"Customer '{customer_name}' "
                f"was deleted."
            )
        )