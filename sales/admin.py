from django.contrib import admin

from .models import SalesOrder, SalesOrderItem
@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'value', 'status', 'created_by', 'created_on')
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name')
    list_filter = ('status', 'created_on')
    ordering = ('-created_on',)



@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'added_on']
    search_fields = ['order', 'product', 'added_on']
    list_filter = ['product', 'added_on']
    ordering = ('-added_on',)