from django.db import models
from django.contrib.auth.models import User


class GeneratedReport(models.Model):

    FORMAT_CHOICES = [
        ("PDF", "PDF"),
        ("Excel", "Excel"),
        ("CSV", "CSV"),
    ]

    STATUS_CHOICES = [
        ("Generated", "Generated"),
        ("Failed", "Failed"),
    ]

    report_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    report_name = models.CharField(
        max_length=100
    )

    export_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES
    )

    date_from = models.DateField(
        null=True,
        blank=True
    )

    date_to = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Generated"
    )

    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_reports"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    downloaded_at = models.DateTimeField(
        null=True,
        blank=True
    )


    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.report_id:

            self.report_id = f"REP{self.id:04d}"

            super().save(
                update_fields=["report_id"]
            )


    def __str__(self):

        return f"{self.report_id} - {self.report_name}"