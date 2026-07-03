from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from invoices.models import Invoice
from customers.models import Customer
from products.models import Product
from authentication.models import UserSession


# ==========================================
# USER DASHBOARD
# ==========================================

class DashboardView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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


# ==========================================
# ADMIN DASHBOARD
# ==========================================

class AdminDashboardView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Admin permission check
        if not request.user.is_staff:
            return Response(
                {
                    "error": "Access Denied"
                },
                status=403
            )

        # ==========================================
        # KPI DATA
        # ==========================================

        total_users = User.objects.count()

        active_users = User.objects.filter(
            is_active=True
        ).count()

        total_revenue = (
            Invoice.objects.aggregate(
                total=Sum("grand_total")
            )["total"] or 0
        )

        total_reports = Invoice.objects.count()


        # ==========================================
        # RECENT REGISTRATIONS
        # ==========================================

        recent_users = User.objects.order_by(
            "-date_joined"
        )[:5]

        recent_data = []

        for user in recent_users:

            recent_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "role": "admin" if user.is_staff else "user"
            })


        # ==========================================
        # LOGGED-IN USERS
        # ==========================================

        online_sessions = (
            UserSession.objects
            .filter(is_online=True)
            .select_related("user")
            .order_by("-login_time")
        )

        logged_users = []

        for session in online_sessions:

            user = session.user

            logged_users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": "admin" if user.is_staff else "user"
            })


        # ==========================================
        # MONTHLY REVENUE
        # ==========================================

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


        # ==========================================
        # RECENT REPORTS
        # ==========================================

        recent_reports = []

        reports = (
            Invoice.objects
            .select_related("customer")
            .order_by("-created_at")[:5]
        )

        for report in reports:

            recent_reports.append({
                "invoice_number": report.invoice_number,
                "customer": report.customer.full_name,
                "amount": float(report.grand_total),
                "status": report.status,
                "date": report.invoice_date.strftime("%d-%m-%Y")
            })


        # ==========================================
        # SYSTEM LOGS
        # ==========================================

        system_logs = []

        for report in reports:

            system_logs.append({
                "title": f"Invoice {report.invoice_number} created",

                "time": timezone.localtime(
                    report.created_at
                ).strftime("%d-%m-%Y %I:%M %p")
            })


        # ==========================================
        # RESPONSE
        # ==========================================

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "total_revenue": float(total_revenue),
            "reports": total_reports,

            "recent_users": recent_data,

            "logged_users": logged_users,

            "monthly_revenue": monthly,

            "recent_reports": recent_reports,

            "system_logs": system_logs
        })