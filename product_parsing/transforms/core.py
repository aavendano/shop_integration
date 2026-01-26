from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, Optional

from .registry import register_transform


@register_transform("trim")
def trim(value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("trim expects a string")
    return value.strip()


@register_transform("upper")
def upper(value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("upper expects a string")
    return value.upper()


@register_transform("parse_price")
def parse_price(value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("parse_price expects a numeric value") from exc
    if not isinstance(value, str):
        raise ValueError("parse_price expects a string or numeric value")

    cleaned = value.replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        raise ValueError("parse_price could not parse a number")
    try:
        return Decimal(match.group(0))
    except InvalidOperation as exc:
        raise ValueError("parse_price expects a numeric value") from exc


@register_transform("map_category")
def map_category(value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("map_category expects a string")
    if not params or "mapping" not in params:
        raise ValueError("map_category requires a mapping param")

    mapping = params["mapping"]
    if not isinstance(mapping, dict):
        raise ValueError("map_category mapping must be a dict")

    return mapping.get(value, value)
