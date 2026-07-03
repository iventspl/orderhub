from django.forms import ModelForm
from .models import Warehouse
from inventory.models import Product
from django import forms

class WarehouseForm(ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'city', 'state', 'zip_code', 'country', 'notes', 'warehouse_type']
        widgets = {
            'warehouse_type': forms.Select(choices=Warehouse.WarehouseType.choices),
            'notes': forms.Textarea(attrs={'placeholder': 'Optional warehouse notes'}),
            'state': forms.TextInput(attrs={'placeholder': 'State/Province'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'ZIP/Postal Code'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country'}),   
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'address': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'name': forms.TextInput(attrs={'placeholder': 'Warehouse name'}),
        }
        labels = {
            'name': 'Warehouse Name',
            'address': 'Address',
            'city': 'City',
            'state': 'State/Province',
            'zip_code': 'ZIP/Postal Code',
            'country': 'Country',
            'notes': 'Notes',
            'warehouse_type': 'Warehouse Type',
        }
        help_texts = {
            'name': 'Enter the name of the warehouse.',
            'address': 'Enter the street address of the warehouse.',
            'city': 'Enter the city where the warehouse is located.',
            'state': 'Enter the state or province where the warehouse is located.',
            'zip_code': 'Enter the ZIP or postal code for the warehouse location.',
            'country': 'Enter the country where the warehouse is located.',
            'notes': 'Add any additional notes or information about this warehouse.',
            'warehouse_type': 'Select whether this is a main warehouse or a shop warehouse.',
        }