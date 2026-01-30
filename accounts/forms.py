from django import forms
from .models import Shop

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = [
            'myshopify_domain', 'domain', 'name', 
            'currency', 'client_id', 'client_secret'
        ]
        widgets = {
            'myshopify_domain': forms.TextInput(attrs={'class': 'input', 'placeholder': 'example.myshopify.com'}),
            'domain': forms.TextInput(attrs={'class': 'input', 'placeholder': 'example.com'}),
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Shop Name'}),
            'currency': forms.TextInput(attrs={'class': 'input', 'placeholder': 'USD'}),
            'client_id': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Shopify Client ID'}),
            'client_secret': forms.PasswordInput(render_value=True, attrs={'class': 'input', 'placeholder': 'Shopify Client Secret'}),
        }
