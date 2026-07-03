from django.contrib import admin
from .models import Transfer

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_warehouse', 'destination_warehouse', 'item_count', 'created_by', 'created_on')
    list_filter = ('source_warehouse', 'destination_warehouse')
    search_fields = ('source_warehouse__name', 'destination_warehouse__name', 'transfer_products__product_name', 'created_by__username')
    ordering = ('-created_on',)

    def item_count(self, obj):
        return obj.transfer_products.count()

    item_count.short_description = 'Items'