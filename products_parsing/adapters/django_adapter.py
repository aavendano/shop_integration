from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Dict, Iterable, Optional

from django.db import transaction
from django.utils.text import slugify

from products_parsing.canonical.schema import (
    CanonicalAttributes,
    CanonicalImage,
    CanonicalProduct,
    CanonicalVariant,
)
from shopify_sync.models import Image, Metafield, Product, Variant


DEFAULT_NAMESPACE = "canonical"
DEFAULT_PRODUCT_TYPE = "Uncategorized"


@dataclass
class PersistOptions:
    session: object
    unique_identifier: str = "identifiers.sku"
    metafield_namespace: str = DEFAULT_NAMESPACE
    sync_metafields: bool = True


@dataclass
class PersistSummary:
    products_created: int = 0
    products_updated: int = 0
    variants_created: int = 0
    variants_updated: int = 0
    images_created: int = 0
    images_updated: int = 0
    metafields_created: int = 0
    metafields_updated: int = 0


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
        if options.sync_metafields:
            created_count, updated_count = _sync_metafields(product, record, options)
            summary.metafields_created += created_count
            summary.metafields_updated += updated_count


def _upsert_product(record: CanonicalProduct, options: PersistOptions):
    product = _resolve_product(record, options)
    defaults = _build_product_defaults(record)

    if product is None:
        # Let Django auto-generate the id
        defaults.update({"session": options.session})
        product = Product.objects.create(**defaults)
        return product, True

    for field, value in defaults.items():
        setattr(product, field, value)
    product.save()
    return product, False


def _build_product_defaults(record: CanonicalProduct) -> Dict[str, object]:
    title = record.basic_info.title or ""
    handle = slugify(title) or slugify(record.identifiers.sku or "")
    product_type = (
        record.classification.product_type
        or record.classification.category
        or DEFAULT_PRODUCT_TYPE
    )
    tags = ", ".join(record.classification.tags) if record.classification.tags else ""

    return {
        "title": title,
        "body_html": record.basic_info.description_html or "",
        "vendor": record.basic_info.brand,
        "product_type": product_type,
        "tags": tags,
        "handle": handle,
    }


def _resolve_product(record: CanonicalProduct, options: PersistOptions) -> Optional[Product]:
    identifier = _get_identifier_value(record, options.unique_identifier)
    if identifier is None:
        raise ValueError("Missing unique identifier for product resolution")

    if options.unique_identifier in {"sku", "identifiers.sku"}:
        variant = (
            Variant.objects.select_related("product")
            .filter(session=options.session, sku=identifier)
            .first()
        )
        return variant.product if variant else None

    field = _PRODUCT_LOOKUP_FIELDS.get(options.unique_identifier)
    if not field:
        raise ValueError("Unsupported unique identifier")
    return Product.objects.filter(session=options.session, **{field: identifier}).first()


def _get_identifier_value(record: CanonicalProduct, identifier: str) -> Optional[str]:
    if identifier in {"sku", "identifiers.sku"}:
        return record.identifiers.sku
    if identifier == "handle":
        return slugify(record.basic_info.title or "") or None
    if identifier == "basic_info.title":
        return record.basic_info.title
    if identifier == "basic_info.brand":
        return record.basic_info.brand
    if identifier == "classification.product_type":
        return record.classification.product_type
    return None


_PRODUCT_LOOKUP_FIELDS = {
    "handle": "handle",
    "basic_info.title": "title",
    "basic_info.brand": "vendor",
    "classification.product_type": "product_type",
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
        if variant_record.sku:
            variant = Variant.objects.filter(
                product=product, session=options.session, sku=variant_record.sku
            ).first()

        if variant is None:
            # Let Django auto-generate the id
            variant = Variant(
                session=options.session,
                product=product,
            )
            created += 1
        else:
            updated += 1

        _update_variant_fields(variant, variant_record)
        variant.save()

    return created, updated


def _update_variant_fields(variant: Variant, record: CanonicalVariant) -> None:
    variant.sku = record.sku
    variant.title = record.title
    variant.price = _safe_decimal(record.price)
    variant.compare_at_price = _safe_decimal(record.compare_at_price)
    variant.barcode = record.barcode
    variant.inventory_quantity = record.inventory_quantity
    variant.grams = 0

    options = list(record.option_values.values()) if record.option_values else []
    variant.option1 = options[0] if len(options) > 0 else None
    variant.option2 = options[1] if len(options) > 1 else None
    variant.option3 = options[2] if len(options) > 2 else None


def _sync_images(
    product: Product, record: CanonicalProduct
) -> tuple[int, int]:
    if not record.media.images:
        return 0, 0

    created = 0
    updated = 0
    for image_record in record.media.images:
        if not image_record.url:
            continue
        image = Image.objects.filter(product=product, src=image_record.url).first()
        if image is None:
            # Let Django auto-generate the id
            image = Image(
                session=product.session,
                product=product,
            )
            created += 1
        else:
            updated += 1

        image.src = image_record.url
        image.position = image_record.position or 1
        image.save()

    return created, updated


def _sync_metafields(
    product: Product, record: CanonicalProduct, options: PersistOptions
) -> tuple[int, int]:
    created = 0
    updated = 0

    attributes = record.attributes
    if not isinstance(attributes, CanonicalAttributes):
        return created, updated

    for key, value in attributes.values.items():
        if key is None:
            continue
        key_str = str(key)[:30]
        namespace = options.metafield_namespace[:20]
        metafield = Metafield.objects.filter(
            product=product, namespace=namespace, key=key_str
        ).first()

        if metafield is None:
            # Let Django auto-generate the id
            metafield = Metafield(
                session=product.session,
                product=product,
                owner_id=product.id,
                owner_resource=Metafield.OWNER_RESOURCE_PRODUCT,
            )
            created += 1
        else:
            updated += 1

        metafield.namespace = namespace
        metafield.key = key_str
        metafield.value_type = Metafield.VALUE_TYPE_STRING
        metafield.value = _serialize_value(value)
        metafield.save()

    return created, updated


def _serialize_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=True)
    except TypeError:
        return str(value)




def _safe_decimal(value: Optional[Decimal]) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(value)


def _safe_int(value: Optional[int], fallback: int = 0) -> int:
    if value is None:
        return fallback
    return int(value)
