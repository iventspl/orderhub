from django.conf import settings
from django.db import models
from django.db.models import Sum

class Product(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sku', 'product_location'], name='unique_sku_per_location')
        ]

    class ProductCategory(models.TextChoices):
        ELECTRONICS = 'electronics', 'Electronics'
        CLOTHING = 'clothing', 'Clothing'
        HOME = 'home', 'Home & Kitchen'
        TOYS = 'toys', 'Toys & Games'
        BOOKS = 'books', 'Books'
        BEAUTY = 'beauty', 'Beauty & Personal Care'
        SPORTS = 'sports', 'Sports & Outdoors'
        AUTOMOTIVE = 'automotive', 'Automotive'
        FOOD = 'food', 'Food & Grocery'
        OTHER = 'other', 'Other'

    category = models.CharField(max_length=50, choices=ProductCategory.choices, default=ProductCategory.OTHER)

    """Model representing a product in the inventory."""
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)  
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reserved_quantity = models.PositiveIntegerField(default=0)  # Quantity reserved for orders but not yet shipped
    stock_quantity = models.PositiveIntegerField(default=0)
    product_location = models.ForeignKey('warehouse.Warehouse', on_delete=models.CASCADE)
    bin_location = models.CharField(max_length=255, blank=True, null=True)  # Optional field for more specific location details
    product_image = models.ImageField(upload_to='product_images/', blank=True, null=True)  # Optional field for product image

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name
    

    def _get_quantity_for_warehouse_type(self, warehouse_type):
        qs = Product.objects.filter(sku=self.sku, product_location__warehouse_type=warehouse_type, company_id=self.company_id)

        stock_total = qs.aggregate(total_stock=Sum('stock_quantity'))['total_stock'] or 0
        reserved_total = qs.aggregate(total=Sum('reserved_quantity'))['total'] or 0

        return max(stock_total - reserved_total, 0)
    

    def get_store_quantity(self):
        return self._get_quantity_for_warehouse_type(self.product_location.WarehouseType.SHOP)

    def get_main_quantity(self):
        return self._get_quantity_for_warehouse_type(self.product_location.WarehouseType.MAIN)
    
    def get_total_quantity(self):
        return self._get_quantity_for_warehouse_type(self.product_location.WarehouseType.MAIN) + self._get_quantity_for_warehouse_type(self.product_location.WarehouseType.SHOP)