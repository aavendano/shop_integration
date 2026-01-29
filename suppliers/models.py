from django.db import models
from shopify_sync.models import Variant

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    product_data_source = models.CharField(max_length=500, null=True, blank=True)
    inventory_data_source = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=100)
    upc = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    imported = models.BooleanField(default=False)
    shopify_variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, related_name='supplier_product')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    