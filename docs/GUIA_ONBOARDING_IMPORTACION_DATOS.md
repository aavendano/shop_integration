# Guía de onboarding: importación de datos (products_parsing)

Esta guía explica **cómo funciona la importación de datos** usando la lógica de la carpeta `products_parsing`, paso a paso y con foco educativo. Está pensada para programadores con conocimientos básicos de Python y sin experiencia previa en mapeo de datos.

## 1) Mapa mental rápido (qué hace el sistema)

El flujo completo es un ETL simple:

1. **Extract (cargar registros)**: se leen registros crudos desde CSV o JSON.
2. **Transform (parseo + normalización)**: cada campo del proveedor se mapea a un esquema canónico con reglas y transformaciones.
3. **Load (persistencia)**: el esquema canónico se guarda en los modelos Django/Shopify.

La entrada es *un archivo con datos del proveedor* y la salida son *productos y variantes actualizados en la base de datos*.

## 2) Secuencia de operaciones (paso a paso)

### 2.1 Carga de registros

El pipeline espera una lista de diccionarios (`Iterable[dict]`). Si parte de archivos, `load_records_from_json` entiende:

- **CSV**: usa la primera fila como headers y genera un dict por fila.
- **JSON**: soporta un array completo o JSON Lines (una línea por registro).【F:products_parsing/pipeline.py†L11-L71】

### 2.2 Carga de configuración del proveedor

`load_provider_config()` lee un JSON de configuración que define **mappings** (origen → destino), **transformaciones** y la política de errores. El JSON se valida (tipos, campos requeridos, etc.).【F:products_parsing/config/loader.py†L1-L188】

### 2.3 Parseo (mapeo + transformaciones)

`parse_records()` recorre cada registro y por cada regla:

1. Extrae el valor en la ruta `source` (con soporte para campos anidados usando `.`).
2. Aplica transformaciones en orden (por ejemplo `trim`, `parse_price`).
3. Asigna el valor al destino canónico (`destination`).
4. Si hay error, se registra en un `ParseReport` y la política define si se continúa o falla.

Este motor es genérico: sólo depende del JSON de configuración y de las transformaciones disponibles.【F:products_parsing/parser/engine.py†L1-L188】

### 2.4 Persistencia (adaptador Django)

Una vez que existen productos canónicos, se guarda todo con `persist_records()`:

- **Producto**: busca si ya existe (por `sku` u otro identificador) y actualiza/crea.
- **Variantes**: se sincronizan por SKU de proveedor.
- **Imágenes**: se sincronizan por URL.
- **Inventario**: actualiza `InventoryItem`/`InventoryLevel` con stock/costo.

Todo se ejecuta dentro de transacciones para mantener consistencia.【F:products_parsing/adapters/django_adapter.py†L1-L239】

### 2.5 Orquestación final

`run_pipeline()` une todo:

1. Carga config.
2. Ejecuta `parse_records()`.
3. Persiste los resultados.

Devuelve un `PersistSummary` y un `ParseReport` para saber qué pasó.【F:products_parsing/pipeline.py†L11-L30】

## 3) Contenido de la carpeta `products_parsing` (carpeta por carpeta)

### `products_parsing/canonical/`
Define el **esquema canónico** (la “forma estándar” de un producto en este sistema). Aquí se centralizan los campos que se usan en todo el proceso.

- `schema.py`: contiene `CanonicalProduct` y subestructuras (identificadores, pricing, inventory, media, variantes, etc.), además de funciones de validación opcional.【F:products_parsing/canonical/schema.py†L1-L220】

> **Idea clave**: cada proveedor puede traer datos distintos, pero todos terminan convertidos a este mismo modelo canónico.

### `products_parsing/config/`
Se encarga de **cargar y validar la configuración** del proveedor.

- `loader.py`: define las clases `ProviderConfig`, `MappingRule` y `TransformSpec`, además de la validación del JSON.【F:products_parsing/config/loader.py†L1-L188】
- `provider_mapping.schema.json`: JSON Schema de referencia para validar los archivos de mapeo.【F:products_parsing/config/provider_mapping.schema.json†L1-L38】

### `products_parsing/parser/`
Es el **motor de parseo**. Ejecuta reglas, transforma, asigna y registra errores.

- `engine.py`: lógica central de parsing + asignación de campos.【F:products_parsing/parser/engine.py†L1-L188】
- `errors.py`: define `ParseReport`, `ParseError` y `ParseFailure` para trazabilidad.【F:products_parsing/parser/errors.py†L1-L30】

### `products_parsing/transforms/`
Agrupa las **transformaciones** disponibles.

- `core.py`: transformaciones básicas como `trim`, `upper`, `parse_price` y `map_category`。【F:products_parsing/transforms/core.py†L1-L68】
- `registry.py`: registro central para aplicar transformaciones por nombre.【F:products_parsing/transforms/registry.py†L1-L39】

### `products_parsing/adapters/`
Contiene la **persistencia hacia Django/Shopify**.

- `django_adapter.py`: traduce el producto canónico a los modelos de Django, creando/actualizando productos, variantes e imágenes.【F:products_parsing/adapters/django_adapter.py†L1-L239】

### `products_parsing/pipeline.py`
Orquestador principal: carga config + parsea + persiste.【F:products_parsing/pipeline.py†L11-L30】

## 4) ¿Cómo definir clases canónicas?

La definición de clases canónicas vive en `canonical/schema.py`. Cada sección agrupa un bloque de datos:

- `CanonicalIdentifiers`: SKU, UPC/EAN, MPN.
- `CanonicalBasicInfo`: título, descripción, marca.
- `CanonicalPricing`: costo, MSRP, MAP, moneda.
- `CanonicalInventory`: stock, almacén.
- `CanonicalClassification`: categoría, tags, género, tipo.
- `CanonicalVariant`: variante (precio, barcode, opciones).
- `CanonicalMedia`: imágenes.
- `CanonicalAttributes`: atributos arbitrarios (clave-valor).

Estas clases son **dataclasses** simples para mantener una estructura predecible en todo el pipeline.【F:products_parsing/canonical/schema.py†L1-L89】

## 5) ¿Cómo definir adaptadores?

Actualmente se usa `django_adapter.py`, que toma un `CanonicalProduct` y lo guarda en modelos Django/Shopify. El adaptador se encarga de:

- Resolver si el producto ya existe (usando `unique_identifier`).
- Crear/actualizar variantes e imágenes.
- Sincronizar inventario asociado.

Esto separa claramente la lógica de parsing de la persistencia en base de datos.【F:products_parsing/adapters/django_adapter.py†L1-L239】

## 6) ¿Cómo definir configuración (mapeo)?

El JSON de configuración define cómo un campo del proveedor se transforma y asigna.

**Estructura base** (ver `ProviderConfig`):

- `provider_id`: identificador del proveedor.
- `error_policy`: `continue` o `fail`.
- `mappings`: lista de reglas (`source`, `destination`, `transforms`, `default`).
- `transform_params`: parámetros compartidos por transformaciones.

La validación se realiza en `load_provider_config_from_dict()` antes de usar el archivo.【F:products_parsing/config/loader.py†L1-L188】

## 7) ¿Cómo funciona el parseo?

`parse_records()` aplica la configuración así:

1. **Extrae** el valor con `_extract_value()` usando rutas tipo `campo.subcampo`.
2. **Transforma** con `_apply_transforms()` en orden.
3. **Asigna** al destino con `_assign_value()` (maneja `variants`, `media` y `attributes`).
4. **Registra errores** con `ParseReport` si algo falla.

El resultado final es un `CanonicalProduct` por registro.【F:products_parsing/parser/engine.py†L1-L188】

## 8) ¿Cómo funciona la transformación?

Las transformaciones están registradas por nombre y se invocan desde el motor:

- `trim`: elimina espacios alrededor.
- `upper`: convierte a mayúsculas.
- `parse_price`: convierte texto/numérico en `Decimal`.
- `map_category`: mapea categorías usando un diccionario.

Cada transformación valida tipos y puede lanzar errores si el valor no es compatible.【F:products_parsing/transforms/core.py†L1-L68】

## 9) Ejemplo didáctico completo (CSV simple)

Supongamos este CSV:

```csv
SKU,Title,Cost,Price,ImageURL
ABC-001,Guantes de invierno,"$12.50","$19.99",https://...
```

Configuración JSON mínima:

```json
{
  "provider_id": "mi_proveedor",
  "error_policy": "continue",
  "mappings": [
    {"source": "SKU", "destination": "identifiers.sku", "transforms": [{"name": "trim"}]},
    {"source": "Title", "destination": "basic_info.title"},
    {"source": "Cost", "destination": "pricing.cost", "transforms": [{"name": "parse_price"}]},
    {"source": "Price", "destination": "variants.0.price", "transforms": [{"name": "parse_price"}]},
    {"source": "ImageURL", "destination": "media.images.0.url"}
  ]
}
```

Resultado: un `CanonicalProduct` con SKU, título, costo, precio de variante e imagen principal. Luego el adaptador crea/actualiza el producto y sus variantes en la base de datos.

## 10) Cheatsheet (referencia rápida)

### Destinos canónicos comunes

- `identifiers.sku`
- `identifiers.upc_ean`
- `basic_info.title`
- `basic_info.description_html`
- `basic_info.brand`
- `pricing.cost`
- `pricing.msrp`
- `pricing.currency`
- `inventory.quantity`
- `classification.category`
- `classification.tags`
- `variants.0.price`
- `variants.0.barcode`
- `media.images.0.url`
- `attributes.color` (o cualquier clave)

### Transformaciones disponibles

- `trim`
- `upper`
- `parse_price`
- `map_category`

### Estructura mínima de config JSON

```json
{
  "provider_id": "mi_proveedor",
  "mappings": [
    {"source": "SKU", "destination": "identifiers.sku"}
  ]
}
```

### Reglas rápidas

- Cada `source` es un nombre de columna (CSV) o un path (JSON).
- `destination` usa el esquema canónico (puntos para anidación).
- `variants.N` y `media.images.N` requieren índice numérico (`0`, `1`, `2`, ...).
- Si una transformación falla, se registra en `ParseReport`.

## 11) Consejos prácticos para usuarios nuevos

1. **Empieza simple**: mapea solo SKU + título + precio.
2. **Valida con pocas filas** antes de importar miles.
3. **Usa `parse_price`** cuando un precio venga con símbolos.
4. **Revisa `ParseReport`** si notas datos faltantes.
5. **Documenta el mapping**: te ayuda a mantenerlo en el tiempo.

---

Si necesitas crear nuevas transformaciones, se agregan en `products_parsing/transforms/` y se registran con `@register_transform` para que el motor pueda usarlas.【F:products_parsing/transforms/core.py†L1-L68】【F:products_parsing/transforms/registry.py†L1-L39】
