from django.db import models
import shopify

from ..encoders import ShopifyDjangoJSONEncoder, empty_list
from .base import ShopifyResourceModel
from .collect import Collect


class SmartCollection(ShopifyResourceModel):
    shopify_resource_class = shopify.resources.SmartCollection

    body_html = models.TextField(null=True)
    handle = models.CharField(max_length=255)
    image = models.JSONField(null=True, encoder=ShopifyDjangoJSONEncoder)
    published_at = models.DateTimeField(null=True)
    published_scope = models.CharField(max_length=16, default="global")
    rules = models.JSONField(
        default=empty_list, encoder=ShopifyDjangoJSONEncoder)
    disjunctive = models.BooleanField(default=False)
    sort_order = models.CharField(max_length=16)
    template_suffix = models.CharField(max_length=32, null=True)
    title = models.CharField(max_length=255)
    updated_at = models.DateTimeField()

    class Meta:
        app_label = "shopify_sync"

    @property
    def collects(self):
        return Collect.objects.filter(self.user, collection_id=self.id)
