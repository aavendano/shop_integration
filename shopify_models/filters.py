import django_filters
from .models import Product


from django import forms

class ProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        lookup_expr='icontains', label='Title',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Search by title...'}))
    vendor = django_filters.CharFilter(
        lookup_expr='icontains', label='Vendor',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Search by vendor...'}))
    product_type = django_filters.CharFilter(
        lookup_expr='icontains', label='Product Type',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Search by type...'}))
    tags = django_filters.CharFilter(
        lookup_expr='icontains', label='Tags',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Search by tags...'}))

    class Meta:
        model = Product
        fields = ['title', 'vendor', 'product_type', 'tags']
