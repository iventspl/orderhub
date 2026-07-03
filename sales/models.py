from django.conf import settings
from django.db import models
from django.utils import timezone

class SalesOrder(models.Model):

    class SalesOrderStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_WAREHOUSE = 'IN WAREHOUSE', 'In Warehouse'
        PACKED = 'PACKED', 'Packed'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class SalesShipTo(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        STORE = 'STORE', 'Store'

    class SalesPaymentMethod(models.TextChoices):
        ON_DELIVERY = 'ON DELIVERY', 'On Delivery'
        AT_STORE = 'AT STORE', 'At Store'
        PAID = 'PAID', 'Paid'
        PREPAID = 'PREPAID', 'Prepaid'
        NET_7 = 'NET 7', 'Net 7'
        NET_14 = 'NET 14', 'Net 14'
        NET_30 = 'NET 30', 'Net 30'


    order_number = models.CharField(max_length=100, unique=True, blank=True, null=True) # auto generate order number
    value = models.DecimalField( max_digits=10, decimal_places=2, default=0.00)
    items = models.ManyToManyField('inventory.Product', through="SalesOrderItem")
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(choices=SalesOrderStatus.choices, default='DRAFT', max_length=20, blank=True, null=True)
    ship_to = models.CharField(choices=SalesShipTo.choices, default='STORE', max_length=20, blank=True, null=True)
    ship_address = models.CharField(blank=True, null=True, max_length=255) #set default to store address ( warehouse address ) if not selected ship to customer
    tracking = models.ForeignKey('tracking.Tracking', on_delete=models.SET_NULL, blank=True, null=True) 
    notes = models.TextField(blank=True, null=True, max_length=500)
    payment_method = models.CharField(choices=SalesPaymentMethod.choices, default='AT STORE', max_length=20)
    payment_status = models.BooleanField(default=False, blank=True, null=True)
    paid_on = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='sales_orders')

    # extra info

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Order {self.order_number} - {self.customer}"
    

    def generate_order_number(self):
        today = timezone.now().strftime('%Y%m%d')
        self.order_number = f"SO-{today}-{self.pk:04d}"
        self.save(update_fields=['order_number'])

    def calculate_value(self):
        # we use self.salesorderitem_set to get all the related SalesOrderItem instances for this SalesOrder
        total = sum(
            ((item.product.price if item.product_id and item.product else 0) * item.quantity)
            for item in self.salesorderitem_set.select_related('product').all()
        )
        SalesOrder.objects.filter(id=self.id).update(value=total)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.generate_order_number()
        if self.value is None or self.value == 0:
            self.calculate_value()
   
    def set_store_address(self):
        # Implement logic to set the store address as the default shipping address if ship_to is STORE
        pass

    def set_customer_address(self):
        # Implement logic to set the customer's address as the shipping address if ship_to is CUSTOMER
        pass




class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    # Snapshot – preserved even after product is deleted from warehouse
    product_sku = models.CharField(max_length=100, blank=True, default='')
    product_name = models.CharField(max_length=255, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    reserved_from_assigned = models.PositiveIntegerField(default=0)
    reserved_from_main = models.PositiveIntegerField(default=0)

    added_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='sales_order_items')

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