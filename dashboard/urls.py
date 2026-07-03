from django.urls import path

from .views import (
    DashboardView,
    AdminDashboardView,
)

urlpatterns = [

    path(
        "",
        DashboardView.as_view(),
        name="dashboard"
    ),

    path(
        "admin/",
        AdminDashboardView.as_view(),
        name="admin-dashboard"
    ),

]