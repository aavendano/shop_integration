import logging
from django.db import models
from decimal import Decimal
from .encoders import ShopifyDjangoJSONEncoder


class ShopifyDataModel(models.Model):
    shopify_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True, primary_key=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        app_label = "shopify_models"
        abstract = True


class Image(ShopifyDataModel):
    position = models.IntegerField(null=True, default=1)
    product = models.ForeignKey(
        "shopify_models.Product", on_delete=models.CASCADE)
    src = models.URLField()

    def __str__(self):
        return self.src


class InventoryItem(ShopifyDataModel):
    sku = models.CharField(max_length=255, null=True)
    tracked = models.BooleanField(default=True)
    requires_shipping = models.BooleanField(default=False)

    unit_cost_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True
    )
    unit_cost_currency = models.CharField(max_length=3, null=True)
    locations_count = models.IntegerField(null=True)
    variant = models.OneToOneField(
        "shopify_models.Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_item",
    )

    @classmethod
    def normalize_unit_cost(cls, unit_cost):
        if not unit_cost:
            return None, None
        amount = unit_cost.get("amount")
        currency = unit_cost.get("currencyCode")
        if amount is None:
            return None, currency
        return Decimal(str(amount)), currency


class Location(ShopifyDataModel):

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    activatable = models.BooleanField(default=False)
    deactivatable = models.BooleanField(default=False)
    deletable = models.BooleanField(default=False)
    fulfills_online_orders = models.BooleanField(default=False)
    has_active_inventory = models.BooleanField(default=False)
    has_unfulfilled_orders = models.BooleanField(default=False)
    ships_inventory = models.BooleanField(default=False)
    address = models.JSONField(
        encoder=ShopifyDjangoJSONEncoder,
        null=True,
    )
    local_pickup_settings = models.JSONField(
        encoder=ShopifyDjangoJSONEncoder,
        null=True,
    )
    last_inventory_sync_at = models.DateTimeField(null=True)

    class Meta:
        app_label = "shopify_sync"

    def trigger_inventory_sync(
        self,
        *,
        updated_at_query=None,
        page_size=50,
        max_pages=None,
        throttle=True,
        quantity_names=None,
    ):
        from .services.inventory import sync_location_inventory_levels

        return sync_location_inventory_levels(
            self,
            updated_at_query=updated_at_query,
            page_size=page_size,
            max_pages=max_pages,
            throttle=throttle,
            quantity_names=quantity_names,
        )


log = logging.getLogger(__name__)


class Product(ShopifyDataModel):
    body_html = models.TextField(default="", null=True)
    handle = models.CharField(max_length=255, db_index=True)
    product_type = models.CharField(max_length=255, db_index=True)
    published_at = models.DateTimeField(null=True)
    published_scope = models.CharField(max_length=64, default="global")
    tags = models.CharField(max_length=255, blank=True)
    template_suffix = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=255, db_index=True)
    vendor = models.CharField(max_length=255, db_index=True, null=True)

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
        self.tags = ", ".join(tag_list if isinstance(
            tag_list, list) else [tag_list])
        return self.tags

    tag_list = property(_get_tag_list, _set_tag_list)

    def __str__(self):
        return self.title


class InventoryLevel(ShopifyDataModel):

    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="inventory_levels")

    quantities = models.JSONField(
        encoder=ShopifyDjangoJSONEncoder,
        null=True,
    )
    can_deactivate = models.BooleanField(default=False)
    deactivation_alert = models.TextField(null=True)
    scheduled_changes = models.JSONField(
        encoder=ShopifyDjangoJSONEncoder,
        null=True,
    )
    sync_pending = models.BooleanField(default=False)
    source_updated_at = models.DateTimeField(null=True)
    synced_at = models.DateTimeField(null=True)


class Variant(ShopifyDataModel):
    barcode = models.CharField(max_length=255, null=True)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    fulfillment_service = models.CharField(max_length=32, default="manual")
    grams = models.IntegerField()
    inventory_management = models.CharField(
        max_length=32, null=True, default="blank")
    inventory_policy = models.CharField(
        max_length=32, null=True, default="deny")
    inventory_quantity = models.IntegerField(null=True)
    option1 = models.CharField(max_length=255, null=True)
    option2 = models.CharField(max_length=255, null=True)
    option3 = models.CharField(max_length=255, null=True)
    position = models.IntegerField(null=True, default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    requires_shipping = models.BooleanField(default=True)
    sku = models.CharField(max_length=255, null=True)
    taxable = models.BooleanField(default=True)
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.product} - {self.title}"
