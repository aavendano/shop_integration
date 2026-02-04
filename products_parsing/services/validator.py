from dataclasses import dataclass
import numbers
from typing import Any, Iterable, List, Sequence

from products_parsing.canonical.schema_v2 import (
    CanonicalImage,
    CanonicalProduct,
    CanonicalVariant,
)


@dataclass
class ValidationIssue:
    path: str
    message: str


class CanonicalValidator:
    def __init__(
        self,
        required_fields: Sequence[str] = ("title",),
    ) -> None:
        self._required_fields = required_fields

    def validate(self, product: CanonicalProduct) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for field_path in self._required_fields:
            value = _get_nested_value(product, field_path)
            if _is_missing(value):
                issues.append(
                    ValidationIssue(path=field_path,
                                    message="Missing required value")
                )

        _validate_optional_string(product.title, "title", issues)
        _validate_optional_string(product.description, "description", issues)
        _validate_optional_string(product.vendor, "vendor", issues)
        _validate_optional_string(product.product_type, "product_type", issues)
        _validate_optional_string(product.handle, "handle", issues)
        _validate_optional_string(product.tags, "tags", issues)
        _validate_metadata(product.metadata, "metadata", issues)

        _validate_variants(product.variants, issues)
        _validate_images(product.images, issues)
        return issues


def _get_nested_value(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
            continue
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


def _validate_optional_bool(value: Any, path: str, issues: List[ValidationIssue]) -> None:
    if value is None:
        return
    if not isinstance(value, bool):
        issues.append(ValidationIssue(path=path, message="Expected boolean"))


def _validate_images(images: Any, issues: List[ValidationIssue]) -> None:
    if images is None:
        return
    if not isinstance(images, list):
        issues.append(ValidationIssue(path="images", message="Expected list"))
        return
    for idx, image in enumerate(images):
        if not isinstance(image, CanonicalImage):
            issues.append(
                ValidationIssue(
                    path=f"images[{idx}]", message="Expected CanonicalImage")
            )
            continue
        _validate_optional_string(image.src, f"images[{idx}].src", issues)
        _validate_optional_int(
            image.position, f"images[{idx}].position", issues)


def _validate_variants(variants: Any, issues: List[ValidationIssue]) -> None:
    if variants is None:
        return
    if not isinstance(variants, list):
        issues.append(ValidationIssue(
            path="variants", message="Expected list"))
        return
    for idx, variant in enumerate(variants):
        if not isinstance(variant, CanonicalVariant):
            issues.append(
                ValidationIssue(
                    path=f"variants[{idx}]", message="Expected CanonicalVariant"
                )
            )
            continue
        _validate_optional_string(
            variant.supplier_sku, f"variants[{idx}].supplier_sku", issues
        )
        _validate_optional_string(
            variant.barcode, f"variants[{idx}].barcode", issues)
        _validate_optional_number(
            variant.price, f"variants[{idx}].price", issues)
        _validate_optional_number(
            variant.compare_at_price, f"variants[{idx}].compare_at_price", issues
        )
        _validate_optional_string(
            variant.option1, f"variants[{idx}].option1", issues)
        _validate_optional_string(
            variant.option2, f"variants[{idx}].option2", issues)
        _validate_optional_string(
            variant.option3, f"variants[{idx}].option3", issues)
        _validate_optional_string(
            variant.title, f"variants[{idx}].title", issues)
        _validate_optional_int(variant.grams, f"variants[{idx}].grams", issues)
        _validate_optional_int(
            variant.position, f"variants[{idx}].position", issues)
        _validate_optional_bool(
            variant.taxable, f"variants[{idx}].taxable", issues)
        _validate_optional_bool(
            variant.requires_shipping, f"variants[{idx}].requires_shipping", issues
        )
        _validate_optional_string(
            variant.inventory_policy, f"variants[{idx}].inventory_policy", issues
        )
        _validate_optional_string(
            variant.inventory_management,
            f"variants[{idx}].inventory_management",
            issues,
        )
        _validate_optional_string(variant.sku, f"variants[{idx}].sku", issues)
        _validate_optional_bool(
            variant.tracked, f"variants[{idx}].tracked", issues)
        _validate_optional_number(
            variant.cost, f"variants[{idx}].cost", issues)
        _validate_optional_int(
            variant.quantity, f"variants[{idx}].quantity", issues)
        _validate_metadata(
            variant.metadata, f"variants[{idx}].metadata", issues)
        _validate_optional_number(
            variant.unit_cost, f"variants[{idx}].unit_cost", issues)
        _validate_optional_number(
            variant.msrp, f"variants[{idx}].msrp", issues)
        _validate_optional_number(variant.map, f"variants[{idx}].map", issues)


def _validate_metadata(
    metadata: Any, path: str, issues: List[ValidationIssue]
) -> None:
    if metadata is None:
        return
    if not isinstance(metadata, dict):
        issues.append(ValidationIssue(path=path, message="Expected dict"))
        return
    for key in metadata:
        if not isinstance(key, str):
            issues.append(ValidationIssue(
                path=path, message="Metadata keys must be strings"))
            break


def validate_products(
    products: Iterable[CanonicalProduct],
    required_fields: Sequence[str] = ("title",),
) -> List[ValidationIssue]:
    validator = CanonicalValidator(required_fields=required_fields)
    issues: List[ValidationIssue] = []
    for product in products:
        issues.extend(validator.validate(product))
    return issues
