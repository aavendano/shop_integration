import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Title')
    vendor = django_filters.CharFilter(lookup_expr='icontains', label='Vendor')
    product_type = django_filters.CharFilter(
        lookup_expr='icontains', label='Product Type')
    tags = django_filters.CharFilter(lookup_expr='icontains', label='Tags')

    class Meta:
        model = Product
        fields = ['title', 'vendor', 'product_type', 'tags']
