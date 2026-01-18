from django.db import models
import shopify

from ..encoders import ShopifyDjangoJSONEncoder
from .base import ShopifyDatedResourceModel


class Webhook(ShopifyDatedResourceModel):
    shopify_resource_class = shopify.resources.Webhook

    topic = models.CharField(max_length=64)
    address = models.URLField()
    format = models.CharField(max_length=4)
    fields = models.JSONField(null=True, encoder=ShopifyDjangoJSONEncoder)
    metafield_namespaces = models.JSONField(
        null=True, encoder=ShopifyDjangoJSONEncoder)

    class Meta:
        app_label = "shopify_sync"
