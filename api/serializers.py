from rest_framework import serializers
from sales.models import SalesOrder, SalesOrderItem
from customers.models import Customer
from tracking.models import Tracking


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'first_name', 'last_name', 'email',
                  'city', 'address', 'zip_code', 'country', 'phone_number']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


class SalesOrderItemSerializer(serializers.ModelSerializer):
    resolved_name = serializers.SerializerMethodField()
    resolved_sku  = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrderItem
        fields = ['id', 'resolved_sku', 'resolved_name', 'quantity',
                  'reserved_from_assigned', 'reserved_from_main']

    def get_resolved_name(self, obj):
        return obj.resolved_name

    def get_resolved_sku(self, obj):
        return obj.resolved_sku


class TrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracking
        fields = ['tracking_number', 'carrier', 'status']


class SalesOrderSerializer(serializers.ModelSerializer):
    customer             = CustomerSerializer(read_only=True)
    salesorderitem_set   = SalesOrderItemSerializer(many=True, read_only=True)
    tracking             = TrackingSerializer(read_only=True)
    payment_method_display = serializers.SerializerMethodField()
    created_on           = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'value', 'status',
            'payment_method', 'payment_method_display',
            'notes', 'ship_address', 'created_on',
            'customer', 'salesorderitem_set', 'tracking',
        ]

    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()
