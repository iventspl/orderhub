from django.conf import settings
from django.db import models


class Product(models.Model):
    """Model representing a product in the inventory."""
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)  # Stock Keeping Unit, unique identifier for the product
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    product_location = models.ForeignKey('warehouse.Warehouse', on_delete=models.SET_NULL, blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name