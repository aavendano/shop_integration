from django import forms
from .models import Variant


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = [
            'supplier_sku', 'title', 'price', 'compare_at_price',
            # 'inventory_quantity', 
            'barcode', 'grams',
            'option1', 'option2', 'option3',
            'requires_shipping', 'taxable'
        ]
        widgets = {
            'supplier_sku': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Supplier SKU'}),
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Variant Title'}),
            'price': forms.NumberInput(attrs={'class': 'input', 'placeholder': '0.00', 'step': '0.01'}),
            'compare_at_price': forms.NumberInput(attrs={'class': 'input', 'placeholder': '0.00', 'step': '0.01'}),
            # 'inventory_quantity': forms.NumberInput(attrs={'class': 'input', 'placeholder': '0'}),
            'barcode': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Barcode'}),
            'grams': forms.NumberInput(attrs={'class': 'input', 'placeholder': '0'}),
            'option1': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Option 1'}),
            'option2': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Option 2'}),
            'option3': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Option 3'}),
            'requires_shipping': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'taxable': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }
