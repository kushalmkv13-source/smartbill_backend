from django.urls import path

from .views import (
    dashboard_report,
    admin_reports,
    download_report,
    business_analytics,
)


urlpatterns = [

    # USER DASHBOARD REPORT
    path(
        "reports/dashboard/",
        dashboard_report,
        name="dashboard-report"
    ),

    # ADMIN REPORTS
    path(
        "admin/reports/",
        admin_reports,
        name="admin-reports"
    ),

    # ADMIN REPORT DOWNLOAD
    path(
        "admin/reports/<int:report_id>/download/",
        download_report,
        name="download-report"
    ),

    # ADMIN BUSINESS ANALYTICS
    path(
        "admin/business-analytics/",
        business_analytics,
        name="business-analytics"
    ),

]