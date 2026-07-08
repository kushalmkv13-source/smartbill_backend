from django.db import models
from django.contrib.auth.models import User

from customers.models import Customer
from products.models import Product


# =====================================================
# INVOICE MODEL
# =====================================================

class Invoice(models.Model):

    PAYMENT_CHOICES = [
        ("Cash", "Cash"),
        ("UPI", "UPI"),
        ("Card", "Card"),
        ("Bank", "Bank"),
    ]

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Unpaid", "Unpaid"),
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Cancelled", "Cancelled"),
    ]


    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invoices"
    )


    invoice_number = models.CharField(
        max_length=30
    )


    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="invoices"
    )


    invoice_date = models.DateField()


    due_date = models.DateField(
        blank=True,
        null=True
    )


    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES
    )


    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    gst_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Draft"
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "user",
                    "invoice_number"
                ],
                name="unique_invoice_number_per_user"
            )

        ]

        ordering = [
            "-id"
        ]


    def __str__(self):

        return self.invoice_number


# =====================================================
# INVOICE ITEM MODEL
# =====================================================

class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items"
    )


    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="invoice_items"
    )


    quantity = models.PositiveIntegerField()


    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    gst = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )


    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    def __str__(self):

        return (
            f"{self.invoice.invoice_number} - "
            f"{self.product.product_name}"
        )