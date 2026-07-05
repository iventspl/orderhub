from django import forms
from django.db.models import Min
from django.forms import ModelForm, inlineformset_factory
from .models import SalesOrder, SalesOrderItem
from customers.models import Customer
from inventory.models import Product
from django_select2.forms import ModelSelect2Widget


class SalesOrderForm(ModelForm):
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            self.fields['customer'].queryset = Customer.objects.filter(company_id=company_id).order_by('first_name', 'last_name')
        else:
            self.fields['customer'].queryset = Customer.objects.none()

    class Meta:
        model = SalesOrder
        fields = ['customer', 'status','ship_to','ship_address','notes', 'payment_method', 'paid_on']

        widgets = {
            'customer': forms.Select(attrs={'id': 'id_customer' }),
            'ship_to': forms.Select(attrs={'id': 'id_ship_to'}),
            'ship_address': forms.TextInput(attrs={'id': 'id_ship_address'}),
        }
        labels = {
            'customer': 'Customer',
            'status': 'Order Status',
            'ship_to': 'Ship To',
            'ship_address': 'Shipping Address',
            'notes': 'Notes',
            'payment_method': 'Payment Method',
            'paid_on': 'Paid On',
        }
        help_texts = {
            'customer': 'Select the customer for this order.',
            'status': 'Select the current status of the order.',
            'ship_to': 'Choose where to ship the order.',
            'ship_address': 'Enter the shipping address if different from the customer\'s address.',
            'notes': 'Add any additional notes or instructions for this order.',
            'payment_method': 'Select the payment method for this order.',
            'paid_on': 'Enter the date and time when the order was paid, if applicable.',
        }


class SalesOrderItemForm(forms.ModelForm):
    class Meta:
        model = SalesOrderItem
        fields = ['product', 'quantity']

    widgets ={
        'product': forms.Select(attrs={'class': 'product-select'}),
    }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        valid_warehouse_ids = kwargs.pop('valid_warehouse_ids', None)
        super().__init__(*args, **kwargs)

        if company_id:
            qs = Product.objects.filter(company_id=company_id)
            if valid_warehouse_ids:
                qs = qs.filter(product_location_id__in=valid_warehouse_ids)
            # One row per SKU — prefer the lowest id (stable pick, MAIN tends to be created first)
            unique_ids = (
                qs.values('sku')
                .annotate(min_id=Min('id'))
                .values_list('min_id', flat=True)
            )
            self.fields['product'].queryset = (
                Product.objects.filter(id__in=unique_ids).order_by('name')
            )
        else:
            self.fields['product'].queryset = Product.objects.none()


# This is simplify how to create formset
SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    form=SalesOrderItemForm,
    extra=1,
    can_delete=True,
)



    