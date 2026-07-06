from django import forms
from warehouse.models import Warehouse
from inventory.models import Product
from django.db.models import Min
from .models import Transfer, TransferProduct
from django.forms import inlineformset_factory


class TransferForm(forms.Form):
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)

        if company_id:
            self.fields['source_warehouse'].queryset = Warehouse.objects.filter(company_id=company_id)
            self.fields['destination_warehouse'].queryset = Warehouse.objects.filter(company_id=company_id)
            self.fields['product'].queryset = Product.objects.filter(
                company_id=company_id,
            ).order_by('name', 'sku')
        else:
            self.fields['source_warehouse'].queryset = Warehouse.objects.none()
            self.fields['destination_warehouse'].queryset = Warehouse.objects.none()
            self.fields['product'].queryset = Product.objects.none()

    source_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label='Source Warehouse')
    destination_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label='Destination Warehouse')
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='Product', required=False)
    quantity = forms.IntegerField(min_value=1, label='Quantity to Transfer', required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False, label='Notes')

    widgets = {
        'source_warehouse': forms.Select(attrs={'class': 't-from', 'id': 'id_source_warehouse'}),
        'destination_warehouse': forms.Select(attrs={'class': 't-to', 'id': 'id_destination_warehouse'}),
        'product': forms.Select(attrs={'class': 't-sku', 'id': 'id_product'}),
        'quantity': forms.NumberInput(attrs={'class': 't-qty', 'id': 'id_quantity'}),
        'notes': forms.Textarea(attrs={'class': 't-notes', 'id': 'id_notes', 'rows': 3}),
    }

    labels = {
        'source_warehouse': 'From',
        'destination_warehouse': 'To',
        'product': 'Product',
        'quantity': 'Quantity to Transfer',
        'notes': 'Notes',
    }

    def clean(self):
        cleaned_data = super().clean()
        source_warehouse      = cleaned_data.get("source_warehouse")
        destination_warehouse = cleaned_data.get("destination_warehouse")
        product               = cleaned_data.get("product")
        quantity              = cleaned_data.get("quantity")

        if source_warehouse and destination_warehouse and source_warehouse == destination_warehouse:
            raise forms.ValidationError("Source and destination warehouses must be different.")

        # Only validate product/quantity when the main form carries a product
        # (multi-product transfers send all items via the formset instead)
        if product:
            source_product = None
            if source_warehouse:
                source_product = Product.objects.filter(
                    product_location=source_warehouse,
                    sku=product.sku,
                    company_id=source_warehouse.company_id,
                ).first()
                if not source_product:
                    raise forms.ValidationError("Selected product is not available in source warehouse.")

            if source_warehouse and quantity:
                available = max(source_product.stock_quantity - source_product.reserved_quantity, 0) if source_product else 0
                if available < quantity:
                    raise forms.ValidationError("Insufficient stock in the source warehouse.")

        return cleaned_data
    

class TransferProductForm(forms.ModelForm):
    class Meta:
        model = TransferProduct
        fields = ['product', 'quantity']
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)

        if company_id:
            self.fields['product'].queryset = Product.objects.filter(
                company_id=company_id,
            ).order_by('name', 'sku')
        else:
            self.fields['product'].queryset = Product.objects.none()


TransferProductFormSet = inlineformset_factory(
    Transfer,
    TransferProduct,
    form=TransferProductForm,
    extra=1,
    can_delete=True,
)