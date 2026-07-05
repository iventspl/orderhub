from django import forms
from .models import Product
from warehouse.models import Warehouse
from customers.models import Customer


class AddProductForm(forms.Form):
    def __init__(self,*args, **kwargs):
        self.product_instance = kwargs.pop('product_instance', None)
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            self.fields['product_location'].queryset = Warehouse.objects.filter(company_id=company_id).order_by('name')
        else:
            self.fields['product_location'].queryset = Warehouse.objects.none()

    product_sku = forms.CharField(label='Product SKU', max_length=100, help_text='Unique SKU for the product')
    product_name = forms.CharField(label='Product Name', max_length=255, help_text='Name of the product')
    product_category = forms.ChoiceField(label='Product Category', choices=Product.ProductCategory.choices, help_text='Category of the product')
    product_description = forms.CharField(label='Product Description', widget=forms.Textarea, required=False, help_text='Optional description of the product')
    stock_quantity = forms.IntegerField(label='Stock Quantity', min_value=0, help_text='Initial stock quantity')
    price = forms.DecimalField(label='Price', max_digits=10, decimal_places=2, min_value=0, help_text='Price of the product')
    product_location = forms.ModelChoiceField(label='Warehouse Location', queryset=Warehouse.objects.all(), help_text='Select the warehouse location')
    bin_location = forms.CharField(label='Bin Location', max_length=255, required=False, help_text='Optional specific location within the warehouse')
    product_image = forms.ImageField(label='Product Image', required=False, help_text='Optional image of the product', widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}))
    remove_image = forms.BooleanField(label='Remove current image', required=False)

    def clean(self):
        cleaned_data = super().clean()
        sku = cleaned_data.get('product_sku')
        location = cleaned_data.get('product_location')

        # Only validate uniqueness when adding new product, not when editing
        if sku and location and not self.product_instance:
            if Product.objects.filter(sku=sku, product_location=location).exists():
                self.add_error('product_sku', 'A product with this SKU already exists in the selected warehouse.')

        return cleaned_data