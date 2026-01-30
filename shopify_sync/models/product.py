import logging

from django.db import models
import shopify

from .base import ShopifyDatedResourceModel
from .collect import Collect
from .image import Image
from .metafield import Metafield
from .option import Option
from .session import activate_session
from .variant import Variant

log = logging.getLogger(__name__)


class Product(ShopifyDatedResourceModel):
    shopify_resource_class = shopify.resources.Product
    child_fields = {
        "images": Image,
        "variants": Variant,
        "options": Option,
        "metafields": Metafield,
    }

    body_html = models.TextField(default="", null=True)
    handle = models.CharField(max_length=255, db_index=True)
    product_type = models.CharField(max_length=255, db_index=True)
    published_at = models.DateTimeField(null=True)
    published_scope = models.CharField(max_length=64, default="global")
    tags = models.CharField(max_length=255, blank=True)
    template_suffix = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=255, db_index=True)
    vendor = models.CharField(max_length=255, db_index=True, null=True)

    class Meta:
        app_label = "shopify_sync"

    @property
    def images(self):
        return Image.objects.filter(product_id=self.id)

    @property
    def collects(self):
        return Collect.objects.filter(product_id=self.id)

    @property
    def variants(self):
        return Variant.objects.filter(product_id=self.id)

    @property
    def options(self):
        return Option.objects.filter(product_id=self.id)

    @property
    def metafields(self):
        return Metafield.objects.filter(product_id=self.id)

    @property
    def price(self):
        return (
            min([variant.price for variant in self.variants]),
            max([variant.price for variant in self.variants]),
        )

    @property
    def weight(self):
        return (
            min([variant.grams for variant in self.variants]),
            max([variant.grams for variant in self.variants]),
        )

    def _get_tag_list(self):
        # Tags are comma-space delimited.
        # https://help.shopify.com/api/reference/product#tags-property
        return self.tags.split(", ") if self.tags else []

    def _set_tag_list(self, tag_list):
        # we need to make sure tag_list is a list, if it is not we will make it
        # one and we will use join to save to tags. The idea is that tag_list
        # will match self.tags at all time. DOESN'T AUTO SAVE
        self.tags = ", ".join(tag_list if isinstance(tag_list, list) else [tag_list])
        return self.tags

    tag_list = property(_get_tag_list, _set_tag_list)

    def add_tag(self, tag):
        # Add a tag or a list of tags
        if tag:
            self.tag_list += tag if isinstance(tag, list) else [tag]

    def remove_tag(self, tag):
        # remove all instances of a tag or list of tags
        if tag:
            rm_list = tag if isinstance(tag, list) else [tag]
            self.tag_list = [tag_ for tag_ in self.tag_list if tag_ not in rm_list]

    def clean_for_post(self, shopify_resource):
        shopify_resource = super().clean_for_post(shopify_resource)
        for child_field in self.get_child_fields().keys():
            children = shopify_resource.attributes.get(child_field)
            if not children:
                continue
            for child in children:
                if isinstance(child, shopify.ShopifyResource):
                    child.attributes.pop("id", None)
                    child.attributes.pop("product_id", None)
                else:
                    child.pop("id", None)
                    child.pop("product_id", None)
        return shopify_resource

    def export_to_shopify(self, sync_meta=True):
        """
        Export the product and cascade to its children.
        """
        shopify_resource = self.to_shopify_resource()

        if self.shopify_id is None:
            shopify_resource = self.clean_for_post(shopify_resource)
        else:
            for child_field in self.get_child_fields().keys():
                shopify_resource.attributes.pop(child_field, None)

        with activate_session(shopify_resource, session=self.session) as shopify_resource:
            successful = shopify_resource.save()

        if not successful:
            message = "[Shopify API Errors]: {}".format(
                ",\n".join(shopify_resource.errors.full_messages())
            )
            log.error(message)
            raise Exception(message)

        with activate_session(shopify_resource, session=self.session) as shopify_resource:
            shopify_resource.reload()
            product = self.manager.sync_one(shopify_resource, sync_children=False)

        product.refresh_from_db()

        if hasattr(product, "variants"):
            for variant in product.variants:
                variant.export_to_shopify(clean_parent_id=True)

        if hasattr(product, "images"):
            for image in product.images:
                image.export_to_shopify(clean_parent_id=True)

        if hasattr(product, "options"):
            for option in product.options:
                option.export_to_shopify(clean_parent_id=True)

        if sync_meta and hasattr(product, "metafields"):
            for metafield in product.metafields:
                metafield.owner_resource = Metafield.OWNER_RESOURCE_PRODUCT
                metafield.owner_id = product.shopify_id
                metafield.export_to_shopify(clean_parent_id=True)

        return product

    def save(self, sync_meta=False, *args, **kwargs):
        with activate_session(self) as shopify_resource:
            # only want to sync the metafields if we have it set to true
            metafields = shopify_resource.metafields() if sync_meta else []
            for metafield in metafields:
                defaults = metafield.attributes
                defaults.update({"product": self, "session": self.session})
                instance, created = Metafield.objects.update_or_create(
                    id=defaults["id"], defaults=defaults
                )
                _new = "Created" if created else "Updated"
                log.debug(f"{_new} metafield for product {self} <{instance}>")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
