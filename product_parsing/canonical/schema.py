from dataclasses import dataclass, field
from decimal import Decimal
import numbers
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass
class ValidationIssue:
    path: str
    message: str


@dataclass
class CanonicalIdentifiers:
    sku: Optional[str] = None
    upc_ean: Optional[str] = None
    mpn: Optional[str] = None


@dataclass
class CanonicalBasicInfo:
    title: Optional[str] = None
    description_text: Optional[str] = None
    description_html: Optional[str] = None
    brand: Optional[str] = None


@dataclass
class CanonicalPricing:
    cost: Optional[Decimal] = None
    msrp: Optional[Decimal] = None
    map: Optional[Decimal] = None
    currency: Optional[str] = None


@dataclass
class CanonicalInventory:
    quantity: Optional[int] = None
    warehouse_name: Optional[str] = None


@dataclass
class CanonicalClassification:
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    gender: Optional[str] = None
    product_type: Optional[str] = None


@dataclass
class CanonicalImage:
    url: Optional[str] = None
    position: Optional[int] = None


@dataclass
class CanonicalMedia:
    images: List[CanonicalImage] = field(default_factory=list)


@dataclass
class CanonicalVariant:
    sku: Optional[str] = None
    title: Optional[str] = None
    option_values: Dict[str, str] = field(default_factory=dict)
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    barcode: Optional[str] = None
    inventory_quantity: Optional[int] = None


@dataclass
class CanonicalAttributes:
    values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalProduct:
    identifiers: CanonicalIdentifiers = field(default_factory=CanonicalIdentifiers)
    basic_info: CanonicalBasicInfo = field(default_factory=CanonicalBasicInfo)
    pricing: CanonicalPricing = field(default_factory=CanonicalPricing)
    inventory: CanonicalInventory = field(default_factory=CanonicalInventory)
    classification: CanonicalClassification = field(default_factory=CanonicalClassification)
    media: CanonicalMedia = field(default_factory=CanonicalMedia)
    variants: List[CanonicalVariant] = field(default_factory=list)
    attributes: CanonicalAttributes = field(default_factory=CanonicalAttributes)


DEFAULT_REQUIRED_FIELDS = (
    "identifiers.sku",
    "basic_info.title",
)


def is_valid_canonical_product(
    product: CanonicalProduct, required_fields: Sequence[str] = DEFAULT_REQUIRED_FIELDS
) -> bool:
    return not validate_canonical_product(product, required_fields=required_fields)


def validate_canonical_product(
    product: CanonicalProduct, required_fields: Sequence[str] = DEFAULT_REQUIRED_FIELDS
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    for field_path in required_fields:
        value = _get_nested_value(product, field_path)
        if _is_missing(value):
            issues.append(
                ValidationIssue(
                    path=field_path,
                    message="Missing required value",
                )
            )

    _validate_optional_string(product.identifiers.sku, "identifiers.sku", issues)
    _validate_optional_string(product.identifiers.upc_ean, "identifiers.upc_ean", issues)
    _validate_optional_string(product.identifiers.mpn, "identifiers.mpn", issues)

    _validate_optional_string(product.basic_info.title, "basic_info.title", issues)
    _validate_optional_string(
        product.basic_info.description_text, "basic_info.description_text", issues
    )
    _validate_optional_string(
        product.basic_info.description_html, "basic_info.description_html", issues
    )
    _validate_optional_string(product.basic_info.brand, "basic_info.brand", issues)

    _validate_optional_number(product.pricing.cost, "pricing.cost", issues)
    _validate_optional_number(product.pricing.msrp, "pricing.msrp", issues)
    _validate_optional_number(product.pricing.map, "pricing.map", issues)
    _validate_optional_string(product.pricing.currency, "pricing.currency", issues)

    _validate_optional_int(product.inventory.quantity, "inventory.quantity", issues)
    _validate_optional_string(
        product.inventory.warehouse_name, "inventory.warehouse_name", issues
    )

    _validate_optional_string(product.classification.category, "classification.category", issues)
    _validate_string_list(product.classification.tags, "classification.tags", issues)
    _validate_optional_string(product.classification.gender, "classification.gender", issues)
    _validate_optional_string(
        product.classification.product_type, "classification.product_type", issues
    )

    _validate_images(product.media.images, issues)
    _validate_variants(product.variants, issues)
    _validate_attributes(product.attributes, issues)

    return issues


def _get_nested_value(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _is_number(value: Any) -> bool:
    return isinstance(value, numbers.Number) and not isinstance(value, bool)


def _validate_optional_string(value: Any, path: str, issues: List[ValidationIssue]) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        issues.append(ValidationIssue(path=path, message="Expected string"))


def _validate_optional_number(value: Any, path: str, issues: List[ValidationIssue]) -> None:
    if value is None:
        return
    if not _is_number(value):
        issues.append(ValidationIssue(path=path, message="Expected number"))


def _validate_optional_int(value: Any, path: str, issues: List[ValidationIssue]) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool):
        issues.append(ValidationIssue(path=path, message="Expected integer"))


def _validate_string_list(value: Any, path: str, issues: List[ValidationIssue]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        issues.append(ValidationIssue(path=path, message="Expected list of strings"))
        return
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            issues.append(
                ValidationIssue(
                    path=f"{path}[{idx}]",
                    message="Expected string",
                )
            )


def _validate_images(images: Any, issues: List[ValidationIssue]) -> None:
    if images is None:
        return
    if not isinstance(images, list):
        issues.append(ValidationIssue(path="media.images", message="Expected list"))
        return
    for idx, image in enumerate(images):
        if not isinstance(image, CanonicalImage):
            issues.append(
                ValidationIssue(
                    path=f"media.images[{idx}]",
                    message="Expected CanonicalImage",
                )
            )
            continue
        if image.url is not None and not isinstance(image.url, str):
            issues.append(
                ValidationIssue(
                    path=f"media.images[{idx}].url",
                    message="Expected string",
                )
            )
        if image.position is not None and not isinstance(image.position, int):
            issues.append(
                ValidationIssue(
                    path=f"media.images[{idx}].position",
                    message="Expected integer",
                )
            )


def _validate_variants(variants: Any, issues: List[ValidationIssue]) -> None:
    if variants is None:
        return
    if not isinstance(variants, list):
        issues.append(ValidationIssue(path="variants", message="Expected list"))
        return
    for idx, variant in enumerate(variants):
        if not isinstance(variant, CanonicalVariant):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}]",
                    message="Expected CanonicalVariant",
                )
            )
            continue
        if variant.sku is not None and not isinstance(variant.sku, str):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].sku",
                    message="Expected string",
                )
            )
        if variant.title is not None and not isinstance(variant.title, str):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].title",
                    message="Expected string",
                )
            )
        if variant.option_values is not None and not isinstance(variant.option_values, dict):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].option_values",
                    message="Expected dict",
                )
            )
        if variant.price is not None and not _is_number(variant.price):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].price",
                    message="Expected number",
                )
            )
        if variant.compare_at_price is not None and not _is_number(
            variant.compare_at_price
        ):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].compare_at_price",
                    message="Expected number",
                )
            )
        if variant.barcode is not None and not isinstance(variant.barcode, str):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].barcode",
                    message="Expected string",
                )
            )
        if variant.inventory_quantity is not None and not isinstance(
            variant.inventory_quantity, int
        ):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}].inventory_quantity",
                    message="Expected integer",
                )
            )


def _validate_attributes(attributes: Any, issues: List[ValidationIssue]) -> None:
    if attributes is None:
        return
    if not isinstance(attributes, CanonicalAttributes):
        issues.append(
            ValidationIssue(
                path="attributes",
                message="Expected CanonicalAttributes",
            )
        )
        return
    if not isinstance(attributes.values, dict):
        issues.append(ValidationIssue(path="attributes.values", message="Expected dict"))
        return
    for key in attributes.values:
        if not isinstance(key, str):
            issues.append(
                ValidationIssue(
                    path="attributes.values",
                    message="Attribute keys must be strings",
                )
            )
            break
