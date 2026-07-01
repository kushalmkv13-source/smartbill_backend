from calendar import month_abbr

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from customers.models import Customer
from products.models import Product
from invoices.models import Invoice


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_report(request):

    user = request.user

    # -----------------------------
    # Month Filter
    # -----------------------------
    month = request.GET.get("month")

    invoices = Invoice.objects.filter(user=user)

    if month:
        invoices = invoices.filter(invoice_date__month=month)

    # -----------------------------
    # Dashboard Cards
    # -----------------------------
    total_customers = Customer.objects.filter(user=user).count()

    total_products = Product.objects.filter(user=user).count()

    total_invoices = invoices.count()

    paid_invoices = invoices.filter(status="Paid").count()

    pending_invoices = invoices.filter(status="Pending").count()

    # -----------------------------
    # Revenue
    # -----------------------------
    total_revenue = (
        invoices.aggregate(total=Sum("grand_total"))["total"]
        or 0
    )

    today = timezone.now().date()

    today_revenue = (
        invoices.filter(invoice_date=today)
        .aggregate(total=Sum("grand_total"))["total"]
        or 0
    )

    monthly_revenue = (
        invoices.filter(
            invoice_date__month=today.month,
            invoice_date__year=today.year
        )
        .aggregate(total=Sum("grand_total"))["total"]
        or 0
    )

    # -----------------------------
    # Monthly Revenue Data
    # -----------------------------
    chart_data = (
        invoices
        .annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(total=Sum("grand_total"))
        .order_by("month")
    )

    monthly_data = {}

    for row in chart_data:

        monthly_data[row["month"].month] = float(row["total"])

    revenue_chart = []

    analytics_chart = []

    monthly_table = []

    previous_revenue = None

    for i in range(1, 13):

        revenue = monthly_data.get(i, 0)

        expenses = revenue * 0.30

        profit = revenue - expenses

        gst = revenue * 0.18

        if previous_revenue is None:

            growth = 0

        elif previous_revenue == 0:

            growth = 0

        else:

            growth = (
                (revenue - previous_revenue)
                / previous_revenue
            ) * 100

        revenue_chart.append({

            "month": month_abbr[i],

            "amount": round(revenue, 2)

        })

        analytics_chart.append({

            "month": month_abbr[i],

            "revenue": round(revenue, 2),

            "expenses": round(expenses, 2),

            "profit": round(profit, 2)

        })

        monthly_table.append({

            "month": month_abbr[i],

            "revenue": round(revenue, 2),

            "expenses": round(expenses, 2),

            "profit": round(profit, 2),

            "gst": round(gst, 2),

            "growth": round(growth, 1)

        })

        previous_revenue = revenue

    # -----------------------------
    # GST Chart
    # -----------------------------
    gst_total = (
        invoices.aggregate(total=Sum("gst_amount"))["total"]
        or 0
    )

    gst_chart = {

        "cgst": round(float(gst_total) / 2, 2),

        "sgst": round(float(gst_total) / 2, 2),

        "igst": 0

    }

    # -----------------------------
    # Recent Invoices
    # -----------------------------
    recent = []

    for invoice in invoices.order_by("-id")[:5]:

        recent.append({

            "invoice_number": invoice.invoice_number,

            "customer": invoice.customer.full_name,

            "amount": float(invoice.grand_total),

            "status": invoice.status

        })

    # -----------------------------
    # Insights
    # -----------------------------
    top_product = (
        Product.objects
        .filter(user=user)
        .order_by("-price")
        .first()
    )

    highest_product = "-"

    fastest_category = "-"

    if top_product:

        highest_product = top_product.product_name

        fastest_category = top_product.category

    best_month = "-"

    if analytics_chart:

        best = max(
            analytics_chart,
            key=lambda x: x["revenue"]
        )

        if best["revenue"] > 0:

            best_month = best["month"]

    # -----------------------------
    # API Response
    # -----------------------------
    return Response({

        "total_customers": total_customers,

        "total_products": total_products,

        "total_invoices": total_invoices,

        "paid_invoices": paid_invoices,

        "pending_invoices": pending_invoices,

        "total_revenue": float(total_revenue),

        "today_revenue": float(today_revenue),

        "monthly_revenue": float(monthly_revenue),

        "revenue_chart": revenue_chart,

        "analytics_chart": analytics_chart,

        "monthly_table": monthly_table,

        "gst_chart": gst_chart,

        "recent_invoices": recent,

        "best_sales_month": best_month,

        "highest_revenue_product": highest_product,

        "fastest_growing_category": fastest_category

    })