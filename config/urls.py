from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("authentication.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("customers.urls")),
    path("api/", include("products.urls")),
    path("api/", include("invoices.urls")),
    path(
    "api/reports/",
    include("reports.urls")
),
path(
    "api/dashboard/",
    include("dashboard.urls")
),
path("api/", include("reports.urls")),
]