from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from django.utils.text import slugify

from products_parsing.canonical.schema_v2 import CanonicalProduct, CanonicalVariant
from django.conf import settings

from shopify_models.models import Image, InventoryItem, InventoryLevel, Product, Variant



DEFAULT_PRODUCT_TYPE = "Uncategorized"


@dataclass
class PersistOptions:
    session: object
    unique_identifier: str = "variants.supplier_sku"


@dataclass
class PersistSummary:
    products_created: int = 0
    products_updated: int = 0
    variants_created: int = 0
    variants_updated: int = 0
    images_created: int = 0
    images_updated: int = 0


def persist_records(
    records: Iterable[CanonicalProduct], options: PersistOptions
) -> PersistSummary:
    summary = PersistSummary()
    for record in records:
        _persist_one(record, options, summary)
    return summary


def _persist_one(
    record: CanonicalProduct, options: PersistOptions, summary: PersistSummary
) -> None:
    with transaction.atomic():
        product, created = _upsert_product(record, options)
        if created:
            summary.products_created += 1
        else:
            summary.products_updated += 1

        created, updated = _sync_variants(product, record, options)
        summary.variants_created += created
        summary.variants_updated += updated
        created, updated = _sync_images(product, record)
        summary.images_created += created
        summary.images_updated += updated


def _upsert_product(record: CanonicalProduct, options: PersistOptions):
    """
    Create or update a ``Product`` instance from a canonical record.

    Instead of building a separate defaults dictionary and looping through it,
    this function now assigns the relevant fields directly on the model.
    If the product does not exist, it will be created with the computed values.
    """
    # Compute core fields. Canonical records have already been validated so
    # we can assign values directly without extra checks.
    title: str = record.title or ""
    description: str = record.description or ""
    vendor: Optional[str] = record.vendor
    product_type: str = record.product_type or DEFAULT_PRODUCT_TYPE
    tags: str = record.tags or ""

    # Build a handle using the provided handle, title or primary SKU.
    handle: str = (
        record.handle
        or slugify(title)
        or slugify(_primary_variant_sku(record) or "")
    )

    defaults = {
        "title": title,
        "description": description,
        "vendor": vendor,
        "product_type": product_type,
        "tags": tags,
        "handle": handle,
    }

    if options.unique_identifier in {"supplier_sku", "variants.supplier_sku"}:
        supplier_sku = _primary_variant_sku(record)
        if supplier_sku:
            variant = (
                Variant.objects.select_related("product")
                .filter(supplier_sku=supplier_sku)
                .first()
            )
            if variant:
                product = variant.product
                for field, value in defaults.items():
                    setattr(product, field, value)
                product.save()
                return product, False

        product = Product.objects.create(**defaults)
        return product, True

    if options.unique_identifier == "handle":
        identifier = record.handle
    elif options.unique_identifier == "title":
        identifier = record.title
    elif options.unique_identifier == "vendor":
        identifier = record.vendor
    elif options.unique_identifier == "product_type":
        identifier = record.product_type
    else:
        identifier = None

    if identifier:
        product, created = Product.objects.update_or_create(
            **{options.unique_identifier: identifier},
            defaults=defaults,
        )
        return product, created

    product = Product.objects.create(**defaults)
    return product, True


def _sync_variants(
    product: Product,
    record: CanonicalProduct,
    options: PersistOptions,
) -> tuple[int, int]:
    if not record.variants:
        return 0, 0

    created = 0
    updated = 0
    for variant_record in record.variants:
        defaults = {
            "supplier_sku": variant_record.supplier_sku,
            "title": variant_record.title,
            "price": _safe_decimal(variant_record.price),
            "compare_at_price": _safe_decimal(variant_record.compare_at_price),
            "barcode": variant_record.barcode,
            "grams": variant_record.grams or 0,
            "position": variant_record.position or 1,
            "taxable": variant_record.taxable if variant_record.taxable is not None else True,
            "requires_shipping": (
                variant_record.requires_shipping
                if variant_record.requires_shipping is not None
                else True
            ),
            "inventory_policy": variant_record.inventory_policy,
            "inventory_management": variant_record.inventory_management,
            "option1": variant_record.option1,
            "option2": variant_record.option2,
            "option3": variant_record.option3,
        }

        if variant_record.supplier_sku:
            variant, was_created = Variant.objects.update_or_create(
                product=product,
                supplier_sku=variant_record.supplier_sku,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        else:
            variant = Variant.objects.create(product=product, **defaults)
            created += 1

        inventory_item = _upsert_inventory_item(variant, variant_record)
        _upsert_inventory_level(inventory_item, variant_record)

    return created, updated


def _upsert_inventory_item(variant: Variant, record: CanonicalVariant) -> InventoryItem:
    inventory_item, _created = InventoryItem.objects.update_or_create(
        variant=variant,
        defaults={
            "shopify_sku": record.sku or variant.supplier_sku,
            "tracked": record.tracked if record.tracked is not None else True,
            "requires_shipping": variant.requires_shipping,
            "source_quantity": record.quantity or 0,
            "unit_cost_amount": _safe_decimal(record.cost),
            "unit_cost_currency": settings.PROVIDER_CURRENCY,
        },
    )
    return inventory_item


def _upsert_inventory_level(inventory_item: InventoryItem, record: CanonicalVariant) -> None:
    location_gid = settings.SHOPIFY_DEFAULT_LOCATION
    if not location_gid:
        return
    InventoryLevel.objects.update_or_create(
        inventory_item=inventory_item,
        location_gid=location_gid,
        defaults={
            "quantities": {"available": record.quantity or 0},
            "sync_pending": True,
        },
    )


def _sync_images(
    product: Product, record: CanonicalProduct
) -> tuple[int, int]:
    if not record.images:
        return 0, 0

    created = 0
    updated = 0
    for image_record in record.images:
        if not image_record.src:
            continue
        image, was_created = Image.objects.update_or_create(
            product=product,
            src=image_record.src,
            defaults={"position": image_record.position or 1},
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return created, updated


def _safe_decimal(value: Optional[Decimal]) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(value)


def _primary_variant_sku(record: CanonicalProduct) -> Optional[str]:
    for variant in record.variants:
        if variant.supplier_sku:
            return variant.supplier_sku
    return None
