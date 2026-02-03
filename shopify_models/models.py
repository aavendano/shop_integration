import logging
from decimal import Decimal
from django.db import models
from .encoders import ShopifyDjangoJSONEncoder
from django.conf import settings


log = logging.getLogger(__name__)



class ShopifyDataModel(models.Model):
    shopify_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True, primary_key=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Image(ShopifyDataModel):
    position = models.IntegerField(null=True, default=1)
    product = models.ForeignKey(
        "shopify_models.Product", on_delete=models.CASCADE)
    src = models.URLField()

    def __str__(self):
        return self.src

class Product(ShopifyDataModel):
    description = models.TextField(default="", null=True)
    handle = models.CharField(max_length=255, db_index=True)
    product_type = models.CharField(max_length=255, db_index=True)
    tags = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, db_index=True)
    vendor = models.CharField(max_length=255, db_index=True, null=True)


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

    def export_to_shopify(self):
        """
        Export product and its variants to Shopify.
        Creates or updates the product in Shopify and updates local shopify_ids.
        """
        from accounts.models import Session
        import shopify
        from django.conf import settings
        from shopify_client import ShopifyGraphQLClient
        
        session = Session.objects.first()
        if not session:
            raise Exception("No active Shopify session found")
            
        with shopify.Session.temp(session.site, settings.API_VERSION, session.token):
            # 1. Create/Update Product
            if self.shopify_id:
                try:
                    s_product = shopify.Product.find(self.shopify_id)
                except:
                    s_product = shopify.Product()
            else:
                s_product = shopify.Product()
            
            s_product.title = self.title
            s_product.body_html = self.description or ""
            s_product.vendor = self.vendor
            s_product.product_type = self.product_type
            s_product.tags = self.tags
            
            # Prepare variants
            # Note: This is a basic implementation. For complex variant syncing (options, etc),
            # more logic is needed. Here we try to match existing variants.
            local_variants = list(self.variants.all().order_by('position'))
            s_variants = []
            
            for v in local_variants:
                s_variant = shopify.Variant()
                if v.shopify_id: # Usually shopify_id is the ID part, unrelated to admin_graphql_api_id formatting here
                     s_variant.id = v.shopify_id
                
                s_variant.price = str(v.price)
                s_variant.sku = v.supplier_sku or ""
                s_variant.title = v.title or ""
                s_variant.barcode = v.barcode
                if settings.INVENTORY_TRACKED:
                    s_variant.inventory_management = "shopify"
                else:
                    s_variant.inventory_management = None
                
                # Options
                if v.option1: s_variant.option1 = v.option1
                if v.option2: s_variant.option2 = v.option2
                if v.option3: s_variant.option3 = v.option3
                
                s_variants.append(s_variant)
            
            if s_variants:
                s_product.variants = s_variants

            # Prepare images
            local_images = list(self.images.all().order_by("position"))
            s_images = []
            for image in local_images:
                if not image.src:
                    continue
                s_image = shopify.Image()
                s_image.src = image.src
                s_image.position = image.position or 1
                s_images.append(s_image)

            if s_images:
                s_product.images = s_images

            # Save
            success = s_product.save()
            
            if not success:
                raise Exception(f"Failed to export to Shopify: {s_product.errors.full_messages()}")
                
            # Update local IDs
            self.shopify_id = str(s_product.id)
            self.save()
            
            # Update variant IDs
            # Shopify returns variants in the same order/logic? 
            # We strictly need to map them back to save Admin GraphQL API IDs if we want price sync to work natively
            # But wait, our logic in sync_variant_prices uses shopify_id to construct GID.
            # So we just need to save shopify_id on variants.
            
            # Reload to get canonical data
            s_product = shopify.Product.find(s_product.id)
            
            # Map back to local variants
            # This heuristic assumes strictly same order or SKU matching
            # Since we just sent them, order should be preserved?
            
            for i, s_variant in enumerate(s_product.variants):
                if i < len(local_variants):
                    local_v = local_variants[i]
                    local_v.shopify_id = str(s_variant.id)
                    local_v.admin_graphql_api_id = s_variant.admin_graphql_api_id
                    local_v.save()

            _sync_inventory_item_unit_costs(
                ShopifyGraphQLClient(session.site, session.token, settings.API_VERSION),
                local_variants,
                currency=settings.PROVIDER_CURRENCY,
            )
            _sync_inventory_quantities(
                ShopifyGraphQLClient(session.site, session.token, settings.API_VERSION),
                local_variants,
                location_gid=settings.SHOPIFY_DEFAULT_LOCATION,
            )


def _sync_inventory_item_unit_costs(
    client,
    local_variants,
    *,
    currency: str | None,
):
    if not currency:
        log.warning("PROVIDER_CURRENCY missing; skipping unit cost export.")
        return
    for local_variant in local_variants:
        variant_gid = getattr(local_variant, "admin_graphql_api_id", None)
        if not variant_gid:
            log.warning("Variant %s missing admin_graphql_api_id", local_variant.id)
            continue
        inventory_item = getattr(local_variant, "inventory_item", None)
        if not inventory_item or inventory_item.unit_cost_amount is None:
            continue
        inventory_item_gid = client.get_variant_inventory_item_id(variant_gid)
        if not inventory_item_gid:
            log.warning("No inventory item id for variant %s", variant_gid)
            continue
        errors = client.update_inventory_item_cost(
            inventory_item_id=inventory_item_gid,
            cost=str(inventory_item.unit_cost_amount),
            currency=currency,
        )
        for error in errors:
            log.warning("InventoryItem unit cost update error: %s", error)


def _sync_inventory_quantities(
    client,
    local_variants,
    *,
    location_gid: str,
):
    if not location_gid:
        log.warning("SHOPIFY_DEFAULT_LOCATION missing; skipping inventory sync.")
        return
    debug_inventory = getattr(settings, "DEBUG_INVENTORY_SYNC", False)
    if debug_inventory:
        _debug_validate_location(client, location_gid)
    quantities = []
    for variant in local_variants:
        inventory_item = getattr(variant, "inventory_item", None)
        source_quantity = (
            getattr(inventory_item, "source_quantity", None)
            if inventory_item
            else None
        )
        if debug_inventory:
            log.info(
                "Inventory sync quantity for variant %s: %s",
                getattr(variant, "id", None),
                source_quantity,
            )
        if source_quantity is None:
            continue
        variant_gid = getattr(variant, "admin_graphql_api_id", None)
        if not variant_gid:
            log.warning("Variant %s missing admin_graphql_api_id", variant.id)
            continue
        inventory_item_gid = client.get_variant_inventory_item_id(variant_gid)
        if not inventory_item_gid:
            log.warning("No inventory item id for variant %s", variant_gid)
            continue
        quantities.append(
            {
                "inventoryItemId": inventory_item_gid,
                "locationId": location_gid,
                "quantity": int(source_quantity),
            }
        )

    if not quantities:
        return
    errors = client.set_inventory_quantities(
        name="available",
        reason="correction",
        quantities=quantities,
        ignore_compare_quantity=True,
    )
    for error in errors:
        log.warning("Inventory set quantities error: %s", error)
    if debug_inventory and quantities:
        _debug_verify_inventory_levels(
            client,
            quantities,
            location_gid,
        )


def _debug_validate_location(client, location_gid: str) -> None:
    location = client.get_location(location_gid)
    if not location:
        log.warning("Location gid not found: %s", location_gid)
        return
    log.info("Validated location: %s (%s)", location.get("name"), location.get("id"))


def _debug_verify_inventory_levels(client, quantities, location_gid: str) -> None:
    for item in quantities:
        inventory_item_id = item.get("inventoryItemId")
        if not inventory_item_id:
            continue
        levels = client.get_inventory_levels(
            inventory_item_id=inventory_item_id,
            quantity_names=["available"],
        )
        matched = False
        for edge in levels:
            location = edge.get("node", {}).get("location", {})
            if location.get("id") == location_gid:
                matched = True
                log.info(
                    "Inventory level for %s at %s: %s",
                    inventory_item_id,
                    location.get("name"),
                    edge.get("node", {}).get("quantities"),
                )
        if not matched:
            log.warning(
                "Inventory level missing location %s for item %s",
                location_gid,
                inventory_item_id,
            )



class InventoryItem(ShopifyDataModel):
    shopify_sku = models.CharField(max_length=255, null=True)
    tracked = models.BooleanField(default=True)
    requires_shipping = models.BooleanField(default=False)
    source_quantity = models.IntegerField(null=True)
    unit_cost_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True
    )
    unit_cost_currency = models.CharField(max_length=3, null=True)
    #locations_count = models.IntegerField(null=True)
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

class InventoryLevel(ShopifyDataModel):
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="inventory_levels")
    location_gid = models.CharField(max_length=255, default=settings.SHOPIFY_DEFAULT_LOCATION)
    quantities = models.JSONField(
        encoder=ShopifyDjangoJSONEncoder,
        null=True,
    )
    sync_pending = models.BooleanField(default=False)
    source_updated_at = models.DateTimeField(null=True)
    synced_at = models.DateTimeField(null=True)


class Variant(ShopifyDataModel):
    INVENTORY_POLICY_CHOICES = [
        ("deny", "Deny"),
        ("continue", "Continue"),
    ]
    barcode = models.CharField(max_length=255, null=True)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    inventory_policy = models.CharField(
        max_length=32, null=True, choices=INVENTORY_POLICY_CHOICES, default="deny")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    taxable = models.BooleanField(default=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    supplier_sku = models.CharField(max_length=255, null=True)
    
    # NOTE: fulfillment_service field removed - use settings.SHOPIFY_FULFILLMENT_SERVICE when needed
    grams = models.IntegerField()
    inventory_management = models.CharField(
        max_length=32, null=True, default="blank")
    option1 = models.CharField(max_length=255, null=True)
    option2 = models.CharField(max_length=255, null=True)
    option3 = models.CharField(max_length=255, null=True)
    position = models.IntegerField(null=True, default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    requires_shipping = models.BooleanField(default=True)



    #inventory_quantity = models.IntegerField(null=True)



    def __str__(self):
        return f"{self.product} - {self.title}"
