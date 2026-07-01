from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products"
    )

    product_name = models.CharField(max_length=150)

    sku = models.CharField(max_length=100)

    category = models.CharField(max_length=100)

    hsn_code = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    gst = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00
    )

    stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(
    default=5
)

    unit = models.CharField(
        max_length=20,
        default="pcs"
    )
    

    barcode = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sku"],
                name="unique_sku_per_user"
            )
        ]

    def __str__(self):
        return self.product_name