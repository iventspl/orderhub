from django.db import models
from django.conf import settings

"""
Po utworzeniu pozycji zamówienia (SalesOrderItem) system:

bierze magazyn pracownika z UserProfile.assigned_warehouse

rezerwuje ile się da z assigned warehouse (reserved_quantity rośnie)

brakującą część rezerwuje z MAIN (reserved_quantity w MAIN rośnie)

tworzy PackingOrder tylko dla tej części z MAIN

zapisuje na pozycji zamówienia ile poszło z assigned i ile z MAIN

Po zmianie PackingOrder.status na PACKED:

zdejmuje stock_quantity z produktów MAIN

zdejmuje reserved_quantity z produktów MAIN

oznacza PackingOrder.stock_deducted=True, żeby nie rozliczyć drugi raz

"""

class PackingOrder(models.Model):
    class PackingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        PACKED = 'packed', 'Packed'
        SHIPPED = 'shipped', 'Shipped'

    order = models.OneToOneField('sales.SalesOrder', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=PackingStatus.choices,
        default=PackingStatus.PENDING,
    )
    stock_deducted = models.BooleanField(default=False)
    is_partial = models.BooleanField(default=False)
    is_packed = models.BooleanField(default=False)
    packed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    packed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='packing_orders')
    notes = models.TextField(blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Packing Order for {self.order.order_number} - Status: {self.status}"


    def get_items_to_pack(self):
        items = []
        for item in self.items_to_pack.select_related('product').all():
            items.append({
                'name': item.resolved_name,
                'sku': item.resolved_sku,
                'quantity': item.quantity_required,
                'scanned_quantity': item.quantity_scanned,
            })
        return items
    
    def get_items_to_pack_json(self):
        import json
        return json.dumps(self.get_items_to_pack())

    def get_progress(self):
        """
        Liczy postęp skanowania dla tego zlecenia pakowania.
        Zwraca słownik: percent (0-100), scanned, required.
        Używane w szablonie i JS do rysowania paska postępu.
        """
        items = self.items_to_pack.all()
        total_required = sum(item.quantity_required for item in items)
        total_scanned = sum(item.quantity_scanned for item in items)
        percent = round(total_scanned / total_required * 100) if total_required > 0 else 0
        return {
            'percent': percent,
            'scanned': total_scanned,
            'required': total_required,
        }

    @property
    def progress_color_class(self):
        """
        Zwraca klasę CSS dla koloru paska postępu:
          danger  →  1-49%   (czerwony)
          warning → 50-89%  (żółty)
          info    → 90-99%  (niebieski, domyślny primary)
          success → 100%    (zielony)
        """
        pct = self.get_progress()['percent']
        if pct == 100:
            return 'success'
        if pct >= 90:
            return 'info'
        if pct >= 50:
            return 'warning'
        if pct > 0:
            return 'danger'
        return ''


class PackingOrderItem(models.Model):
    packing_order = models.ForeignKey(PackingOrder, on_delete=models.CASCADE, related_name='items_to_pack')
    sales_order_item = models.ForeignKey('sales.SalesOrderItem', on_delete=models.CASCADE)
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    # Snapshot – preserved even after product is deleted from warehouse
    product_sku = models.CharField(max_length=100, blank=True, default='')
    product_name = models.CharField(max_length=255, blank=True, default='')
    quantity_required = models.PositiveIntegerField(default=0)
    quantity_scanned = models.PositiveIntegerField(default=0)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='packing_order_items')
    def save(self, *args, **kwargs):
        if self.product_id and self.product:
            if not self.product_sku:
                self.product_sku = self.product.sku
            if not self.product_name:
                self.product_name = self.product.name
        super().save(*args, **kwargs)

    @property
    def resolved_sku(self):
        if self.product_id and self.product:
            return self.product.sku
        return self.product_sku

    @property
    def resolved_name(self):
        if self.product_id and self.product:
            return self.product.name
        return self.product_name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['packing_order', 'sales_order_item'], name='unique_packing_item_per_order_item')
        ]


class PackingScanEvent(models.Model):
    """
    Rejestruje każde zdarzenie skanowania przez pracownika.
    Jeden rekord = jeden pracownik + jedna pozycja + ilość + czas.

    Pozwala na:
      - śledzenie kto ile spakował (statystyki per user)
      - audyt: które pozycje były skanowane i kiedy
      - wykrywanie anomalii (zerowe skany, ponowne skanowanie)
    """
    packing_order = models.ForeignKey(
        PackingOrder,
        on_delete=models.CASCADE,
        related_name='scan_events',
    )
    packing_item = models.ForeignKey(
        PackingOrderItem,
        on_delete=models.CASCADE,
        related_name='scan_events',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scan_events',
    )
    quantity = models.PositiveIntegerField()
    scanned_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(
        'users.Company',
        on_delete=models.CASCADE,
        related_name='scan_events',
    )

    def __str__(self):
        username = self.user.username if self.user else '—'
        return f"{username} → {self.packing_item.resolved_sku} ×{self.quantity} ({self.scanned_at:%Y-%m-%d %H:%M})"