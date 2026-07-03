from calendar import month_abbr
import csv
from io import BytesIO

from django.db.models import Sum, Count
from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openpyxl import Workbook

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from customers.models import Customer
from products.models import Product
from invoices.models import Invoice

from .models import GeneratedReport

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from customers.models import Customer
from products.models import Product
from invoices.models import Invoice

from .models import GeneratedReport


# =====================================================
# USER DASHBOARD REPORT
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_report(request):

    user = request.user

    # -----------------------------
    # Month Filter
    # -----------------------------

    month = request.GET.get("month")

    invoices = Invoice.objects.filter(
        user=user
    )

    if month:

        invoices = invoices.filter(
            invoice_date__month=month
        )


    # -----------------------------
    # Dashboard Cards
    # -----------------------------

    total_customers = Customer.objects.filter(
        user=user
    ).count()


    total_products = Product.objects.filter(
        user=user
    ).count()


    total_invoices = invoices.count()


    paid_invoices = invoices.filter(
        status="Paid"
    ).count()


    pending_invoices = invoices.filter(
        status="Pending"
    ).count()


    # -----------------------------
    # Revenue
    # -----------------------------

    total_revenue = (
        invoices.aggregate(
            total=Sum("grand_total")
        )["total"]
        or 0
    )


    today = timezone.localdate()


    today_revenue = (
        invoices.filter(
            invoice_date=today
        )
        .aggregate(
            total=Sum("grand_total")
        )["total"]
        or 0
    )


    monthly_revenue = (
        invoices.filter(
            invoice_date__month=today.month,
            invoice_date__year=today.year
        )
        .aggregate(
            total=Sum("grand_total")
        )["total"]
        or 0
    )


    # -----------------------------
    # Monthly Revenue Data
    # -----------------------------

    chart_data = (
        invoices
        .annotate(
            month=TruncMonth("invoice_date")
        )
        .values("month")
        .annotate(
            total=Sum("grand_total")
        )
        .order_by("month")
    )


    monthly_data = {}


    for row in chart_data:

        monthly_data[
            row["month"].month
        ] = float(row["total"])


    revenue_chart = []

    analytics_chart = []

    monthly_table = []

    previous_revenue = None


    for i in range(1, 13):

        revenue = monthly_data.get(
            i,
            0
        )


        expenses = revenue * 0.30

        profit = revenue - expenses

        gst = revenue * 0.18


        if previous_revenue is None:

            growth = 0

        elif previous_revenue == 0:

            growth = 0

        else:

            growth = (
                (
                    revenue -
                    previous_revenue
                )
                /
                previous_revenue
            ) * 100


        revenue_chart.append(
            {
                "month": month_abbr[i],

                "amount": round(
                    revenue,
                    2
                )
            }
        )


        analytics_chart.append(
            {
                "month": month_abbr[i],

                "revenue": round(
                    revenue,
                    2
                ),

                "expenses": round(
                    expenses,
                    2
                ),

                "profit": round(
                    profit,
                    2
                )
            }
        )


        monthly_table.append(
            {
                "month": month_abbr[i],

                "revenue": round(
                    revenue,
                    2
                ),

                "expenses": round(
                    expenses,
                    2
                ),

                "profit": round(
                    profit,
                    2
                ),

                "gst": round(
                    gst,
                    2
                ),

                "growth": round(
                    growth,
                    1
                )
            }
        )


        previous_revenue = revenue


    # -----------------------------
    # GST Chart
    # -----------------------------

    gst_total = (
        invoices.aggregate(
            total=Sum("gst_amount")
        )["total"]
        or 0
    )


    gst_chart = {

        "cgst": round(
            float(gst_total) / 2,
            2
        ),

        "sgst": round(
            float(gst_total) / 2,
            2
        ),

        "igst": 0

    }


    # -----------------------------
    # Recent Invoices
    # -----------------------------

    recent = []


    recent_invoices = (
        invoices
        .select_related("customer")
        .order_by("-id")[:5]
    )


    for invoice in recent_invoices:

        recent.append(
            {
                "invoice_number":
                    invoice.invoice_number,

                "customer":
                    invoice.customer.full_name,

                "amount":
                    float(invoice.grand_total),

                "status":
                    invoice.status
            }
        )


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

        highest_product = (
            top_product.product_name
        )

        fastest_category = (
            top_product.category
        )


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

    return Response(
        {
            "total_customers":
                total_customers,

            "total_products":
                total_products,

            "total_invoices":
                total_invoices,

            "paid_invoices":
                paid_invoices,

            "pending_invoices":
                pending_invoices,

            "total_revenue":
                float(total_revenue),

            "today_revenue":
                float(today_revenue),

            "monthly_revenue":
                float(monthly_revenue),

            "revenue_chart":
                revenue_chart,

            "analytics_chart":
                analytics_chart,

            "monthly_table":
                monthly_table,

            "gst_chart":
                gst_chart,

            "recent_invoices":
                recent,

            "best_sales_month":
                best_month,

            "highest_revenue_product":
                highest_product,

            "fastest_growing_category":
                fastest_category
        },
        status=status.HTTP_200_OK
    )


# =====================================================
# ADMIN REPORTS MANAGEMENT
# =====================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def admin_reports(request):

    # -----------------------------
    # Admin Check
    # -----------------------------

    if not request.user.is_staff:

        return Response(
            {
                "success": False,
                "message": "Access Denied"
            },
            status=status.HTTP_403_FORBIDDEN
        )


    # =================================================
    # GET REPORTS
    # =================================================

    if request.method == "GET":

        reports = (
            GeneratedReport.objects
            .select_related("generated_by")
            .all()
            .order_by("-created_at")
        )


        total_reports = reports.count()


        exported_reports = reports.filter(
            downloaded_at__isnull=False
        ).count()


        now = timezone.localtime()


        reports_this_month = reports.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).count()


        last_report = reports.first()


        if last_report:

            last_generated = (
                timezone.localtime(
                    last_report.created_at
                )
                .strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            )

        else:

            last_generated = None


        report_history = []


        for report in reports:

            report_history.append(
                {
                    "id":
                        report.id,

                    "report_id":
                        report.report_id,

                    "report_name":
                        report.report_name,

                    "export_format":
                        report.export_format,

                    "date_from":
                        (
                            report.date_from.strftime(
                                "%Y-%m-%d"
                            )
                            if report.date_from
                            else None
                        ),

                    "date_to":
                        (
                            report.date_to.strftime(
                                "%Y-%m-%d"
                            )
                            if report.date_to
                            else None
                        ),

                    "status":
                        report.status,

                    "generated_on":
                        timezone.localtime(
                            report.created_at
                        ).strftime(
                            "%d-%m-%Y"
                        ),

                    "created_at":
                        timezone.localtime(
                            report.created_at
                        ).strftime(
                            "%d-%m-%Y %I:%M %p"
                        ),

                    "downloaded":
                        report.downloaded_at
                        is not None
                }
            )
        # =================================================
        # RECENT DOWNLOADS
        # =================================================

        recent_downloads = []

        downloaded_reports = (
            GeneratedReport.objects
            .filter(downloaded_at__isnull=False)
            .order_by("-downloaded_at")[:5]
        )

        for report in downloaded_reports:

            if report.export_format == "PDF":
                extension = "pdf"

            elif report.export_format == "Excel":
                extension = "xlsx"

            else:
                extension = "csv"

            recent_downloads.append(
                {
                    "id": report.id,

                    "report_id": report.report_id,

                    "report_name": report.report_name,

                    "file_name":
                        f"{report.report_name}.{extension}",

                    "export_format":
                        report.export_format,

                    "downloaded_at":
                        timezone.localtime(
                            report.downloaded_at
                        ).strftime(
                            "%d-%m-%Y %I:%M %p"
                        )
                }
            )

        return Response(
            {
                "success": True,

                "total_reports":
                    total_reports,

                "exported_reports":
                    exported_reports,

                "reports_this_month":
                    reports_this_month,

                "last_generated":
                    last_generated,

                               "reports":
                    report_history,

                "recent_downloads":
                    recent_downloads
            },
            status=status.HTTP_200_OK
        )


    # =================================================
    # GENERATE REPORT
    # =================================================

    if request.method == "POST":

        report_name = request.data.get(
            "report_name"
        )


        export_format = request.data.get(
            "export_format"
        )


        date_from = request.data.get(
            "date_from"
        )


        date_to = request.data.get(
            "date_to"
        )


        # -----------------------------
        # Required Validation
        # -----------------------------

        if not report_name or not export_format:

            return Response(
                {
                    "success": False,

                    "message":
                        "Report type and export format are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # -----------------------------
        # Format Validation
        # -----------------------------

        valid_formats = [
            "PDF",
            "Excel",
            "CSV"
        ]


        if export_format not in valid_formats:

            return Response(
                {
                    "success": False,
                    "message":
                        "Invalid export format."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # -----------------------------
        # Date Validation
        # -----------------------------

        if date_from and date_to:

            if date_from > date_to:

                return Response(
                    {
                        "success": False,

                        "message":
                            "From date cannot be after To date."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # -----------------------------
        # Create Report Record
        # -----------------------------

        report = GeneratedReport.objects.create(

            report_name=report_name,

            export_format=export_format,

            date_from=date_from or None,

            date_to=date_to or None,

            generated_by=request.user,

            status="Generated"

        )


        return Response(
            {
                "success": True,

                "message":
                    "Report generated successfully.",

                "report": {

                    "id":
                        report.id,

                    "report_id":
                        report.report_id,

                    "report_name":
                        report.report_name,

                    "export_format":
                        report.export_format,

                    "status":
                        report.status,

                    "generated_on":
                        timezone.localtime(
                            report.created_at
                        ).strftime(
                            "%d-%m-%Y"
                        )
                }
            },
            status=status.HTTP_201_CREATED
        )
    # =====================================================
# DOWNLOAD GENERATED REPORT
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_report(request, report_id):

    # =====================================================
    # ADMIN CHECK
    # =====================================================

    if not request.user.is_staff:
        return Response(
            {
                "success": False,
                "message": "Access Denied"
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # =====================================================
    # GET REPORT
    # =====================================================

    try:
        report = GeneratedReport.objects.get(
            id=report_id
        )

    except GeneratedReport.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Report not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # =====================================================
    # GET INVOICES
    # =====================================================

    invoices = (
        Invoice.objects
        .select_related("customer")
        .all()
        .order_by("-invoice_date", "-id")
    )

    if report.date_from:
        invoices = invoices.filter(
            invoice_date__gte=report.date_from
        )

    if report.date_to:
        invoices = invoices.filter(
            invoice_date__lte=report.date_to
        )

    invoices = list(invoices)

    # =====================================================
    # PREPARE DATA
    # =====================================================

    headers = [
        "Invoice Number",
        "Invoice Date",
        "Customer",
        "Payment Method",
        "Status",
        "Subtotal",
        "GST",
        "Grand Total",
    ]

    rows = []

    for invoice in invoices:

        rows.append([
            invoice.invoice_number,
            invoice.invoice_date.strftime("%d-%m-%Y"),
            invoice.customer.full_name,
            invoice.payment_method,
            invoice.status,
            float(invoice.subtotal),
            float(invoice.gst_amount),
            float(invoice.grand_total),
        ])

    # =====================================================
    # CSV DOWNLOAD
    # =====================================================

    if report.export_format == "CSV":

        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{report.report_id}.csv"'
        )

        writer = csv.writer(response)

        writer.writerow(headers)

        for row in rows:
            writer.writerow(row)

        report.downloaded_at = timezone.now()

        report.save(
            update_fields=["downloaded_at"]
        )

        return response

    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

    if report.export_format == "Excel":

        workbook = Workbook()

        worksheet = workbook.active

        worksheet.title = "Invoice Report"

        worksheet.append([
            f"InvoiceHub - {report.report_name}"
        ])

        worksheet.append([
            f"Report ID: {report.report_id}"
        ])

        worksheet.append([])

        worksheet.append(headers)

        for row in rows:
            worksheet.append(row)

        widths = {
            "A": 20,
            "B": 16,
            "C": 28,
            "D": 18,
            "E": 14,
            "F": 16,
            "G": 16,
            "H": 18,
        }

        for column, width in widths.items():
            worksheet.column_dimensions[column].width = width

        worksheet.freeze_panes = "A5"

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{report.report_id}.xlsx"'
        )

        workbook.save(response)

        report.downloaded_at = timezone.now()

        report.save(
            update_fields=["downloaded_at"]
        )

        return response

    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

    if report.export_format == "PDF":

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                f"InvoiceHub - {report.report_name}",
                styles["Title"]
            )
        )

        elements.append(
            Spacer(1, 5 * mm)
        )

        elements.append(
            Paragraph(
                f"<b>Report ID:</b> {report.report_id}",
                styles["Normal"]
            )
        )

        elements.append(
            Spacer(1, 5 * mm)
        )

        pdf_data = [headers]

        for row in rows:
            pdf_data.append(
                [str(value) for value in row]
            )

        table = Table(
            pdf_data,
            repeatRows=1,
            colWidths=[
                32 * mm,
                24 * mm,
                40 * mm,
                30 * mm,
                22 * mm,
                25 * mm,
                22 * mm,
                28 * mm,
            ]
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B1B33")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
            ])
        )

        elements.append(table)

        document.build(elements)

        pdf_bytes = buffer.getvalue()

        buffer.close()

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{report.report_id}.pdf"'
        )

        report.downloaded_at = timezone.now()

        report.save(
            update_fields=["downloaded_at"]
        )

        return response

    # =====================================================
    # INVALID FORMAT
    # =====================================================

    return Response(
        {
            "success": False,
            "message": "Unsupported report format."
        },
        status=status.HTTP_400_BAD_REQUEST
    )
# =====================================================
# ADMIN BUSINESS ANALYTICS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_analytics(request):

    # ADMIN CHECK
    if not request.user.is_staff:
        return Response(
            {
                "success": False,
                "message": "Access Denied"
            },
            status=status.HTTP_403_FORBIDDEN
        )

    today = timezone.localdate()
    current_year = today.year

    # TOTAL USERS
    total_users = User.objects.filter(
        is_staff=False
    ).count()

    # TOTAL REVENUE
    total_revenue = (
        Invoice.objects.aggregate(
            total=Sum("grand_total")
        )["total"]
        or 0
    )

    # TOTAL GST
    gst_collected = (
        Invoice.objects.aggregate(
            total=Sum("gst_amount")
        )["total"]
        or 0
    )

    # MONTHLY REVENUE
    revenue_monthly = {
        month_number: 0
        for month_number in range(1, 13)
    }

    invoices_current_year = Invoice.objects.filter(
        invoice_date__year=current_year
    ).values(
        "invoice_date",
        "grand_total",
        "gst_amount"
    )

    # MONTHLY GST
    gst_monthly = {
        month_number: 0
        for month_number in range(1, 13)
    }

    for invoice in invoices_current_year:

        invoice_date = invoice["invoice_date"]

        if invoice_date:

            month_number = invoice_date.month

            revenue_monthly[month_number] += float(
                invoice["grand_total"] or 0
            )

            gst_monthly[month_number] += float(
                invoice["gst_amount"] or 0
            )

    # MONTHLY USER REGISTRATIONS
    users_monthly = {
        month_number: 0
        for month_number in range(1, 13)
    }

    registered_users = User.objects.filter(
        is_staff=False
    ).only("date_joined")

    for registered_user in registered_users:

        joined_date = registered_user.date_joined

        if joined_date and joined_date.year == current_year:

            users_monthly[joined_date.month] += 1


    # CHART DATA
    revenue_chart = []
    user_growth_chart = []
    gst_chart = []
    revenue_vs_gst_chart = []

    for month_number in range(1, 13):

        month_name = month_abbr[month_number]

        revenue_amount = revenue_monthly.get(
            month_number,
            0
        )

        gst_amount = gst_monthly.get(
            month_number,
            0
        )

        users_count = users_monthly.get(
            month_number,
            0
        )

        revenue_chart.append({
            "month": month_name,
            "amount": round(revenue_amount, 2)
        })

        user_growth_chart.append({
            "month": month_name,
            "users": users_count
        })

        gst_chart.append({
            "month": month_name,
            "amount": round(gst_amount, 2)
        })

        revenue_vs_gst_chart.append({
            "month": month_name,
            "revenue": round(revenue_amount, 2),
            "gst": round(gst_amount, 2)
        })


    # BUSINESS GROWTH
    current_month_revenue = revenue_monthly.get(
        today.month,
        0
    )

    if today.month == 1:
        previous_month_revenue = 0
    else:
        previous_month_revenue = revenue_monthly.get(
            today.month - 1,
            0
        )

    if previous_month_revenue > 0:

        business_growth = (
            (
                current_month_revenue
                - previous_month_revenue
            )
            / previous_month_revenue
        ) * 100

    else:
        business_growth = 0


    # USER GROWTH
    current_month_users = users_monthly.get(
        today.month,
        0
    )

    if today.month == 1:
        previous_month_users = 0
    else:
        previous_month_users = users_monthly.get(
            today.month - 1,
            0
        )

    if previous_month_users > 0:

        users_growth = (
            (
                current_month_users
                - previous_month_users
            )
            / previous_month_users
        ) * 100

    else:
        users_growth = 0


    # REVENUE GROWTH
    revenue_growth = business_growth


    # GST GROWTH
    current_month_gst = gst_monthly.get(
        today.month,
        0
    )

    if today.month == 1:
        previous_month_gst = 0
    else:
        previous_month_gst = gst_monthly.get(
            today.month - 1,
            0
        )

    if previous_month_gst > 0:

        gst_growth = (
            (
                current_month_gst
                - previous_month_gst
            )
            / previous_month_gst
        ) * 100

    else:
        gst_growth = 0


    # RESPONSE
    return Response(
        {
            "success": True,

            "total_users": total_users,

            "total_revenue": float(total_revenue),

            "gst_collected": float(gst_collected),

            "business_growth": round(
                business_growth,
                1
            ),

            "users_growth": round(
                users_growth,
                1
            ),

            "revenue_growth": round(
                revenue_growth,
                1
            ),

            "gst_growth": round(
                gst_growth,
                1
            ),

            "revenue_chart": revenue_chart,

            "user_growth_chart":
                user_growth_chart,

            "gst_chart": gst_chart,

            "revenue_vs_gst_chart":
                revenue_vs_gst_chart
        },
        status=status.HTTP_200_OK
    )