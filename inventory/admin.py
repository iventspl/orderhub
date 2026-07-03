from django.contrib import admin

from .models import Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'description', 'price', 'reserved_quantity', 'stock_quantity', 'product_location', 'created_by', 'created_on')
    search_fields = ('sku', 'name', 'description')
    list_filter = ('created_on', 'product_location', 'created_by', 'company')
    ordering = ('-created_on',)
