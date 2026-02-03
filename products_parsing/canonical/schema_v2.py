from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class CanonicalImage:
    src: Optional[str] = None
    position: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    alt: Optional[str] = None


@dataclass
class CanonicalVariant:
    supplier_sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None

    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None

    title: Optional[str] = None
    grams: Optional[int] = None
    position: Optional[int] = None
    taxable: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    inventory_policy: Optional[str] = None
    inventory_management: Optional[str] = None

    sku: Optional[str] = None
    tracked: Optional[bool] = None
    cost: Optional[Decimal] = None
    quantity: Optional[int] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalProduct:
    title: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    handle: Optional[str] = None
    tags: Optional[str] = None

    variants: List[CanonicalVariant] = field(default_factory=list)
    images: List[CanonicalImage] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)
