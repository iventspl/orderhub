from django.conf import settings
from django.db import models

class Tracking(models.Model):
    class TrackingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_WAREHOUSE = 'IN WAREHOUSE', 'In Warehouse'
        PACKED = 'PACKED', 'Packed'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'

    class TrackingCarrier(models.TextChoices):
        UPS = 'UPS', 'UPS'
        FEDEX = 'FEDEX', 'FedEx'
        DHL = 'DHL', 'DHL'
        INPOST = 'INPOST', 'InPost'
        GLS = 'GLS', 'GLS'
        POCZTA_POLSKA = 'POCZTA POLSKA', 'Poczta Polska'
        OTHER = 'OTHER', 'Other'

    tracking_number = models.CharField(max_length=100)
    order = models.ForeignKey('sales.SalesOrder', on_delete=models.CASCADE, related_name='trackings')
    packed_order = models.OneToOneField('packing.PackingOrder', on_delete=models.SET_NULL, blank=True, null=True)
    carrier = models.CharField(choices=TrackingCarrier.choices, max_length=20)
    status = models.CharField(choices=TrackingStatus.choices, max_length=20)
    estimated_delivery = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='trackings')

    def __str__(self):
        return f"{self.carrier} - {self.tracking_number}"