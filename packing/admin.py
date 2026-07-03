from django.contrib import admin
from .models import PackingOrder, PackingScanEvent


@admin.register(PackingScanEvent)
class PackingScanEventAdmin(admin.ModelAdmin):
    list_display = ('scanned_at', 'user', 'packing_order', 'sku', 'quantity')
    list_filter = ('user', 'scanned_at')
    search_fields = ('user__username', 'packing_item__product_sku', 'packing_item__product_name')
    ordering = ('-scanned_at',)
    date_hierarchy = 'scanned_at'

    def sku(self, obj):
        return obj.packing_item.resolved_sku
    sku.short_description = 'SKU'
