from django.conf import settings
from django.db import models


class SalesOrder(models.Model):

    class SalesOrderStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_WAREHOUSE = 'IN WAREHOUSE', 'In Warehouse'
        PACKED = 'PACKED', 'Packed'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        PAID = 'PAID', 'Paid'

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
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, blank=False, null=True)
    status = models.CharField(choices=SalesOrderStatus.choices, default='DRAFT', max_length=20)
    ship_to = models.CharField(choices=SalesShipTo.choices, default='STORE', max_length=20)
    ship_address = models.CharField(blank=True, null=True, max_length=255) #set default to store address ( warehouse address ) if not selected ship to customer
    tracking = models.ForeignKey('tracking.Tracking', on_delete=models.SET_NULL, blank=True, null=True) 
    notes = models.TextField(blank=True, null=True, max_length=500)
    payment_method = models.CharField(choices=SalesPaymentMethod.choices, default='AT STORE', max_length=20)
    payment_status = models.BooleanField(default=False, blank=True, null=True)
    paid_on = models.DateTimeField(blank=True, null=True)

    # extra info

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Order {self.order_number} - {self.customer}"
    

    def generate_order_number(self):
        # Implement logic to generate a unique order number
        pass

    def set_store_address(self):
        # Implement logic to set the store address as the default shipping address if ship_to is STORE
        pass

    def set_customer_address(self):
        # Implement logic to set the customer's address as the shipping address if ship_to is CUSTOMER
        pass




class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT) #create Product model in inventory app
    quantity = models.PositiveIntegerField(default=1)