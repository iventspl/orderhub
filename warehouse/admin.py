from django.contrib import admin
from .models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'zip_code', 'country', 'notes', 'warehouse_type')
    search_fields = ('name', 'address', 'city', 'zip_code', 'country', 'notes', 'warehouse_type')
    list_filter = ('name', 'city', 'created_on', 'warehouse_type')
    ordering = ('-created_on',)

