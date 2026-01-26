from typing import Any, Dict, Iterable, Iterator, List, Optional

from product_parsing.canonical.schema import CanonicalProduct
from product_parsing.config.loader import ProviderConfig
from product_parsing.transforms import apply_transform

from .errors import ParseError, ParseFailure, ParseReport


def parse_records(
    records: Iterable[Dict[str, Any]],
    config: ProviderConfig,
    report: Optional[ParseReport] = None,
) -> Iterator[CanonicalProduct]:
    active_report = report or ParseReport()

    for record_index, record in enumerate(records):
        product = CanonicalProduct()
        for rule in config.mappings:
            try:
                value = _extract_value(record, rule.source)
                if value is None:
                    value = rule.default
                if value is None:
                    continue

                value = _apply_transforms(
                    value,
                    rule,
                    config,
                    active_report,
                    record_index,
                )
                if value is None:
                    continue

                _assign_value(product, rule.destination, value)
            except ParseFailure as exc:
                active_report.record(exc.error)
                raise exc.cause from exc
            except Exception as exc:
                _record_error(
                    active_report,
                    config,
                    record_index,
                    source=rule.source,
                    destination=rule.destination,
                    transform=None,
                    exc=exc,
                )
                if config.error_policy == "fail":
                    raise
        yield product


def _apply_transforms(
    value: Any,
    rule,
    config: ProviderConfig,
    report: ParseReport,
    record_index: int,
) -> Any:
    current_value = value
    for transform in rule.transforms:
        try:
            current_value = apply_transform(
                transform.name,
                current_value,
                params=_merge_transform_params(transform, config),
            )
        except Exception as exc:
            error = ParseError(
                provider_id=config.provider_id,
                record_index=record_index,
                source=rule.source,
                destination=rule.destination,
                transform=transform.name,
                message=str(exc),
            )
            if config.error_policy == "fail":
                raise ParseFailure(error, exc) from exc
            report.record(error)
            return None
    return current_value


def _record_error(
    report: ParseReport,
    config: ProviderConfig,
    record_index: int,
    source: Optional[str],
    destination: Optional[str],
    transform: Optional[str],
    exc: Exception,
) -> None:
    report.record(
        ParseError(
            provider_id=config.provider_id,
            record_index=record_index,
            source=source,
            destination=destination,
            transform=transform,
            message=str(exc),
        )
    )


def _extract_value(record: Dict[str, Any], path: str) -> Any:
    current: Any = record
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]
    return current


def _merge_transform_params(transform, config: ProviderConfig) -> Dict[str, Any]:
    params = dict(config.transform_params.get(transform.name, {}))
    if transform.params:
        params.update(transform.params)
    return params


def _assign_value(product: CanonicalProduct, destination: str, value: Any) -> None:
    parts = destination.split(".")
    if not parts:
        return

    if parts[0] == "variants":
        _assign_variant_value(product, parts[1:], value)
        return

    if parts[0] == "media":
        _assign_media_value(product, parts[1:], value)
        return

    if parts[0] == "attributes":
        _assign_attribute_value(product, parts[1:], value)
        return

    current: Any = product
    for part in parts[:-1]:
        current = getattr(current, part)
    setattr(current, parts[-1], value)


def _assign_variant_value(product: CanonicalProduct, parts: List[str], value: Any) -> None:
    if not parts:
        return
    index = _parse_index(parts[0])
    if index is None:
        return
    if index >= len(product.variants):
        product.variants.extend([_new_variant()] * (index - len(product.variants) + 1))
    variant = product.variants[index]
    if len(parts) == 1:
        return
    if parts[1] == "option_values":
        if len(parts) == 2:
            return
        option_key = parts[2]
        variant.option_values[option_key] = value
        return
    setattr(variant, parts[1], value)


def _assign_media_value(product: CanonicalProduct, parts: List[str], value: Any) -> None:
    if not parts or parts[0] != "images":
        return
    if len(parts) == 1:
        return
    index = _parse_index(parts[1])
    if index is None:
        return
    if index >= len(product.media.images):
        product.media.images.extend(
            [_new_image()] * (index - len(product.media.images) + 1)
        )
    image = product.media.images[index]
    if len(parts) == 2:
        return
    setattr(image, parts[2], value)


def _assign_attribute_value(product: CanonicalProduct, parts: List[str], value: Any) -> None:
    if not parts:
        return
    key = parts[0]
    product.attributes.values[key] = value


def _parse_index(raw: str):
    try:
        return int(raw)
    except ValueError:
        return None


def _new_variant():
    from product_parsing.canonical.schema import CanonicalVariant

    return CanonicalVariant()


def _new_image():
    from product_parsing.canonical.schema import CanonicalImage

    return CanonicalImage()
