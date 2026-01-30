from django.db import models
import shopify

from ..encoders import ShopifyDjangoJSONEncoder, empty_list
from .base import ShopifyResourceModel


class LineItem(ShopifyResourceModel):
    shopify_resource_class = shopify.resources.LineItem
    parent_field = "order_id"

    fulfillable_quantity = models.IntegerField()
    fulfillment_service = models.CharField(max_length=32)
    fulfillment_status = models.CharField(max_length=32, null=True)
    grams = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=256)
    order = models.ForeignKey("shopify_sync.Order", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_id = models.BigIntegerField(null=True)
    product_exists = models.BooleanField(default=True)
    properties = models.JSONField(
        default=empty_list, encoder=ShopifyDjangoJSONEncoder)
    quantity = models.IntegerField()
    requires_shipping = models.BooleanField(default=True)
    sku = models.CharField(max_length=256)
    gift_card = models.BooleanField(default=False)
    taxable = models.BooleanField(default=False)
    tax_lines = models.JSONField(
        default=empty_list, encoder=ShopifyDjangoJSONEncoder)
    title = models.CharField(max_length=256)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2)
    variant_id = models.BigIntegerField(null=True)
    variant_title = models.CharField(max_length=256, null=True)
    vendor = models.CharField(max_length=64, null=True)

    class Meta:
        app_label = "shopify_sync"

    def fix_ids(self):
        from . import Product
        from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
        import logging
        
        logger = logging.getLogger(__name__)
        
        # If product_id is already set, use it to get the product
        if self.product_id:
            try:
                product = Product.objects.get(id=self.product_id)
            except ObjectDoesNotExist:
                logger.error(f"Product with id {self.product_id} not found for LineItem {self.id}")
                return
        else:
            # Try to find product by title, but handle multiple matches
            try:
                product = Product.objects.get(title=self.title)
                self.product_id = product.id
            except MultipleObjectsReturned:
                logger.error(
                    f"Multiple products found with title '{self.title}'. "
                    f"Cannot determine correct product for LineItem {self.id}. "
                    f"Please set product_id manually."
                )
                return
            except ObjectDoesNotExist:
                logger.error(f"No product found with title '{self.title}' for LineItem {self.id}")
                return

        # Fix variant_id
        if len(product.variants) == 1:
            self.variant_id = product.variants[0].id
        else:
            # there is more than one variant, so we look up the title
            try:
                variant = product.variant_set.get(title=self.variant_title)
                self.variant_id = variant.id
            except (MultipleObjectsReturned, ObjectDoesNotExist) as e:
                logger.error(
                    f"Could not find unique variant with title '{self.variant_title}' "
                    f"for product '{product.title}': {str(e)}"
                )
                return
        
        self.save()

    def __str__(self):
        return self.name
