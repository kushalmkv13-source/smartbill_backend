from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from rest_framework.views import APIView
from rest_framework.response import Response

from invoices.models import Invoice
from customers.models import Customer
from products.models import Product


class DashboardView(APIView):

    def get(self, request):

        total_revenue = (
            Invoice.objects.aggregate(
                total=Sum("grand_total")
            )["total"] or 0
        )

        total_invoices = Invoice.objects.count()

        total_customers = Customer.objects.count()

        total_products = Product.objects.count()

        paid = Invoice.objects.filter(
            status="Paid"
        ).count()

        pending = Invoice.objects.filter(
            status="Pending"
        ).count()

        monthly = [0] * 12

        monthly_data = (
            Invoice.objects
            .annotate(month=ExtractMonth("invoice_date"))
            .values("month")
            .annotate(total=Sum("grand_total"))
            .order_by("month")
        )

        for item in monthly_data:

            monthly[item["month"] - 1] = float(item["total"])

        return Response({

            "revenue": float(total_revenue),

            "invoice_count": total_invoices,

            "customers": total_customers,

            "products": total_products,

            "paid": paid,

            "pending": pending,

            "monthly_revenue": monthly

        })