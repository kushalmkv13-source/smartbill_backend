from django.urls import path

from .views import dashboard_report

urlpatterns = [

    path(
        "dashboard/",
        dashboard_report,
        name="dashboard-report"
    ),

]