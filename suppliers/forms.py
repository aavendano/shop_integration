from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'code', 'product_data_source', 'inventory_data_source']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Supplier Name'}),
            'code': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Supplier Code'}),
            'product_data_source': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Data Source URL'}),
            'inventory_data_source': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Data Source URL'}),
        }

class ProductImportForm(forms.Form):
    product_data_file = forms.FileField(
        label='Product Data File (CSV)',
        help_text='Upload a CSV file containing product data',
        widget=forms.FileInput(attrs={'class': 'file-input', 'accept': '.csv'})
    )
