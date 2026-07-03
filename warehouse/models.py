from django.conf import settings
from django.db import models
from inventory.models import Product

class Warehouse(models.Model):
    class WarehouseType(models.TextChoices):
        MAIN = 'MAIN', 'Main Warehouse'
        SHOP = 'SHOP', 'Shop Warehouse'
    
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    warehouse_type = models.CharField(choices=WarehouseType.choices, max_length=20, default=WarehouseType.SHOP)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='warehouses')

    def __str__(self):
        return self.name
    
    def capacity_usage(self):
        # Placeholder logic for capacity usage calculation
        # In a real implementation, this would calculate based on actual inventory and warehouse capacity
        return "72%"
    
    def active_zones(self):
        # Placeholder logic for active zones
        # In a real implementation, this would return the zones that currently have inventory or activity
        return "A, B, C"
    
    def get_warehouse_products(self):
        products = Product.objects.filter(product_location=self, company=self.company)
        # Placeholder logic to get products assigned to this warehouse
        # In a real implementation, this would query the inventory for products located in this warehouse
        return products
