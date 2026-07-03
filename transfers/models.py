from django.db import models
from django.conf import settings


# Create your models here.

class Transfer(models.Model):
    source_warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.CASCADE, related_name='transfers_out')
    destination_warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.CASCADE, related_name='transfers_in')
    items = models.ManyToManyField('inventory.Product', through='TransferProduct')
    notes = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='transfers')

    def __str__(self):
        return f"Transfer {self.id} from {self.source_warehouse.name} to {self.destination_warehouse.name}"
    



class TransferProduct(models.Model):
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='transfer_products')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    product_sku = models.CharField(max_length=100, blank=True, default='')
    product_name = models.CharField(max_length=255, blank=True, default='')
    quantity = models.PositiveIntegerField()

    added_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='transfer_products')


    def save(self, *args, **kwargs):
        if self.product_id and self.product:
            if not self.product_sku:
                self.product_sku = self.product.sku
            if not self.product_name:
                self.product_name = self.product.name
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.quantity} of {self.product.name} for Transfer {self.transfer.id}"