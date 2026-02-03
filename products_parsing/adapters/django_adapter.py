from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Optional

from django.db import transaction
from django.utils.text import slugify

from products_parsing.canonical.schema_v2 import CanonicalProduct, CanonicalVariant
from django.conf import settings

from shopify_models.models import Image, InventoryItem, InventoryLevel, Product, Variant



DEFAULT_NAMESPACE = "canonical"
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
    product = _resolve_product(record, options)
    defaults = _build_product_defaults(record)

    if product is None:
        # Let Django auto-generate the id
        product = Product.objects.create(**defaults)
        return product, True

    for field, value in defaults.items():
        setattr(product, field, value)
    product.save()
    return product, False


def _build_product_defaults(record: CanonicalProduct) -> Dict[str, object]:
    title = record.title or ""
    handle = record.handle or slugify(title) or slugify(_primary_variant_sku(record) or "")
    product_type = record.product_type or DEFAULT_PRODUCT_TYPE
    tags = record.tags or ""

    return {
        "title": title,
        "description": record.description or "",
        "vendor": record.vendor,
        "product_type": product_type,
        "tags": tags,
        "handle": handle,
    }


def _resolve_product(record: CanonicalProduct, options: PersistOptions) -> Optional[Product]:
    identifier = _get_identifier_value(record, options.unique_identifier)
    if identifier is None:
        raise ValueError("Missing unique identifier for product resolution")

    if options.unique_identifier in {"supplier_sku", "variants.supplier_sku"}:
        variant = (
            Variant.objects.select_related("product")
            .filter(supplier_sku=identifier)
            .first()
        )
        return variant.product if variant else None

    field = _PRODUCT_LOOKUP_FIELDS.get(options.unique_identifier)
    if not field:
        raise ValueError("Unsupported unique identifier")
    return Product.objects.filter(**{field: identifier}).first()


def _get_identifier_value(record: CanonicalProduct, identifier: str) -> Optional[str]:
    if identifier in {"supplier_sku", "variants.supplier_sku"}:
        return _primary_variant_sku(record)
    if identifier == "handle":
        return record.handle or slugify(record.title or "") or None
    if identifier == "title":
        return record.title
    if identifier == "vendor":
        return record.vendor
    if identifier == "product_type":
        return record.product_type
    return None


_PRODUCT_LOOKUP_FIELDS = {
    "handle": "handle",
    "title": "title",
    "vendor": "vendor",
    "product_type": "product_type",
}


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
        variant = None
        if variant_record.supplier_sku:
            variant = Variant.objects.filter(
                product=product, supplier_sku=variant_record.supplier_sku
            ).first()

        if variant is None:
            # Let Django auto-generate the id
            variant = Variant(
                product=product,
            )
            created += 1
        else:
            updated += 1

        _update_variant_fields(variant, variant_record)
        variant.save()
        inventory_item = _upsert_inventory_item(variant, variant_record)
        _upsert_inventory_level(inventory_item, variant_record)

    return created, updated


def _update_variant_fields(variant: Variant, record: CanonicalVariant) -> None:
    variant.supplier_sku = record.supplier_sku
    variant.title = record.title
    variant.price = _safe_decimal(record.price)
    variant.compare_at_price = _safe_decimal(record.compare_at_price)
    variant.barcode = record.barcode
    #variant.inventory_quantity = record.inventory_quantity
    variant.grams = record.grams or 0
    variant.position = record.position or 1
    variant.taxable = record.taxable if record.taxable is not None else variant.taxable
    if record.requires_shipping is not None:
        variant.requires_shipping = record.requires_shipping
    variant.inventory_policy = record.inventory_policy or variant.inventory_policy
    variant.inventory_management = (
        record.inventory_management or variant.inventory_management
    )
    variant.option1 = record.option1
    variant.option2 = record.option2
    variant.option3 = record.option3


def _upsert_inventory_item(variant: Variant, record: CanonicalVariant) -> InventoryItem:
    inventory_item, _created = InventoryItem.objects.update_or_create(
        variant=variant,
        defaults={
            "shopify_sku": record.sku or variant.supplier_sku,
            "tracked": record.tracked if record.tracked is not None else True,
            "requires_shipping": variant.requires_shipping,
            "source_quantity": _safe_int(record.quantity, fallback=0),
            "unit_cost_amount": _safe_decimal(record.cost),
            "unit_cost_currency": settings.PROVIDER_CURRENCY,
        },
    )
    return inventory_item


def _upsert_inventory_level(inventory_item: InventoryItem, record: CanonicalVariant) -> None:
    location_gid = settings.SHOPIFY_DEFAULT_LOCATION
    if not location_gid:
        return
    available_quantity = _safe_int(record.quantity, fallback=0)
    InventoryLevel.objects.update_or_create(
        inventory_item=inventory_item,
        location_gid=location_gid,
        defaults={
            "quantities": {"available": available_quantity},
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
        image = Image.objects.filter(
            product=product, src=image_record.src).first()
        if image is None:
            # Let Django auto-generate the id
            image = Image(
                product=product,
            )
            created += 1
        else:
            updated += 1

        image.src = image_record.src
        image.position = image_record.position or 1
        image.save()

    return created, updated


def _safe_decimal(value: Optional[Decimal]) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(value)


def _safe_int(value: Optional[int], fallback: int = 0) -> int:
    if value is None:
        return fallback
    return int(value)


def _primary_variant_sku(record: CanonicalProduct) -> Optional[str]:
    for variant in record.variants:
        if variant.supplier_sku:
            return variant.supplier_sku
    return None
