# Plan de Refactorización: Canonical Model Mirroring ORM

## 1. Diagnóstico
El modelo canónico actual (`CanonicalProduct`) utiliza una estructura jerárquica conceptual (`basic_info`, `pricing`, `inventory`, etc.) que no se alinea con el modelo de persistencia de Django (`Product`, `Variant`, `InventoryItem`), que es relacional y plano.

**Problemas identificados:**
*   **Fricción en ETL:** El "Loader" debe desestructurar objetos anidados para llenar modelos planos.
*   **Ambigüedad:** Campos como `pricing` existen a nivel producto pero en realidad pertenecen a la variante en el ORM.
*   **Verbosidad:** El parser crea estructuras profundas innecesarias que luego se descartan.
*   **Mantenimiento:** Agregar un campo requiere tocar múltiples niveles de anidamiento.

## 2. Principios de Diseño
Para la nueva arquitectura del modelo canónico (`schema_v2.py`), se seguirán estos principios:

1.  **Espejo del ORM:** Las clases canónicas deben mapear 1:1 a los modelos de Django (`Product`, `Variant`).
2.  **Aplanamiento (Flattening):** Eliminar agrupaciones artificiales. Si el campo está en `Variant` en la BD, está en `CanonicalVariant`.
3.  **Inventario en Variante:** Aunque el ORM separa `InventoryItem`, el Canónico tratará los datos de inventario (`cost`, `tracked`, `quantity`) como atributos de la `CanonicalVariant` para simplificar la entrada. El Loader se encargará de la separación.
4.  **Campos Explícitos:** Se eliminan diccionarios genéricos (`option_values`) en favor de campos explícitos (`option1`, `option2`, `option3`).
5.  **DTOs Puros:** Las clases canónicas serán `dataclasses` sin lógica. La validación se mueve a un servicio externo (`CanonicalValidator`).
6.  **Buffer de Metadata:** Datos que no tengan columna en el ORM pero deban persistirse temporalmente irán a un campo `metadata` (JSON).

## 3. Propuesta de Estructura de Clases

### `CanonicalProduct`
Mapea directamente al modelo `Product` de Django.
```python
@dataclass
class CanonicalProduct:
    # Identifiers & Basic Info
    title: Optional[str] = None
    description: Optional[str] = None  # body_html
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    handle: Optional[str] = None
    tags: Optional[str] = None  # String separado por comas, espejo del ORM

    # Relations
    variants: List[CanonicalVariant] = field(default_factory=list)
    images: List[CanonicalImage] = field(default_factory=list)

    # Extra
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### `CanonicalVariant`
Mapea al modelo `Variant` + datos esenciales de `InventoryItem`.
```python
@dataclass
class CanonicalVariant:
    # Identifiers
    supplier_sku: Optional[str] = None  # Mapea a Variant.sku
    barcode: Optional[str] = None

    # Pricing
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None

    # Options (Strict Mapping)
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None

    # Properties
    title: Optional[str] = None
    grams: Optional[int] = None
    position: Optional[int] = None
    taxable: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    inventory_policy: Optional[str] = None
    inventory_management: Optional[str] = None

    # Inventory (Flattened from InventoryItem)
    sku: Optional[str] = None  # shopify_sku (InventoryItem)
    tracked: Optional[bool] = None
    cost: Optional[Decimal] = None  # unit_cost_amount
    quantity: Optional[int] = None  # source_quantity (buffer field)

    # Extra
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### `CanonicalImage`
Mapea al modelo `Image`.
```python
@dataclass
class CanonicalImage:
    src: Optional[str] = None
    position: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    alt: Optional[str] = None
```

## 4. Estrategia de Transición

La refactorización se realizará en fases para minimizar riesgos:

*   **Fase 1: Definición del Schema V2**
    *   Crear `products_parsing/canonical/schema_v2.py` con las nuevas dataclasses.
    *   No tocar el schema actual todavía.

*   **Fase 2: Servicio de Validación**
    *   Crear `products_parsing/services/validator.py`.
    *   Implementar lógica de validación desacoplada de las dataclasses.

*   **Fase 3: Adaptación del Motor de Parsing (`engine.py`)**
    *   Modificar `_assign_value` para soportar asignación plana (sin navegar `pricing.x`).
    *   Soportar flag para usar `schema_v2` o `schema_v1`.

*   **Fase 4: Migración de Mappings (JSON)**
    *   Actualizar los archivos JSON de los proveedores para apuntar a los nuevos destinos (ej: `pricing.cost` -> `variants.cost`).

*   **Fase 5: Actualización del Loader (Django)**
    *   Actualizar el pipeline de persistencia para leer del objeto plano `CanonicalProduct` (V2).
    *   Implementar la lógica que divide `CanonicalVariant` en `Variant` + `InventoryItem`.

*   **Fase 6: Limpieza**
    *   Eliminar `schema.py` original.
    *   Renombrar `schema_v2.py` a `schema.py`.

## 5. Riesgos y Validaciones

*   **Riesgo: Pérdida de Datos en Mappings.**
    *   *Mitigación:* Crear tests unitarios que comparen la salida del parser V1 vs V2 para un mismo input de proveedor, asegurando que todos los valores críticos se transfieren.
*   **Riesgo: Datos de Inventario.**
    *   *Mitigación:* Verificar que la lógica de separación (Variant vs InventoryItem) maneje correctamente casos de updates parciales.
*   **Riesgo: Option Values dinámicos.**
    *   *Validación:* Asegurar que si un proveedor envía más de 3 opciones, el sistema falle grácilmente o concatene valores (según regla de negocio), ya que el ORM solo soporta 3.
