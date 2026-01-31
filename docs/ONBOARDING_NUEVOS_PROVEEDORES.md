# Guía de Onboarding para Nuevos Proveedores

Esta guía explica cómo integrar un nuevo proveedor al sistema de sincronización de productos. El proceso se basa en configuración (archivos JSON) y no requiere programación en Python, salvo casos excepcionales.

## 1. Conceptos Básicos

El sistema funciona tomando un archivo de productos (CSV o JSON) del proveedor y "traduciéndolo" a un formato estándar interno. Esta traducción se define en un archivo de configuración.

-   **Proveedor (Supplier)**: La entidad que suministra los productos. Se identifica por un `code` único (ej. `nalpac`).
-   **Configuración de Mapeo**: Un archivo JSON que dice "la columna A del CSV va al campo B del sistema".
-   **Transformaciones**: Operaciones para limpiar datos (ej. quitar espacios, convertir moneda).

## 2. Paso a Paso

### Paso 1: Obtener y Analizar el Archivo del Proveedor

Consigue un archivo de muestra del proveedor (CSV o JSON). Ábrelo (puedes usar Excel, Google Sheets o un editor de texto) e identifica las columnas clave:

-   Identificador único (SKU, UPC).
-   Nombre del producto.
-   Precio y costo.
-   Inventario (cantidad).
-   Imágenes.
-   Atributos (Color, Talla, etc.).

### Paso 2: Crear el Archivo de Configuración

Crea un nuevo archivo en: `products_parsing/config/providers/<codigo_proveedor>.json`.
*Nota: `<codigo_proveedor>` debe ser minúsculas y sin espacios (ej. `mi_proveedor.json`).*

Estructura base del archivo:

```json
{
  "provider_id": "mi_proveedor",
  "error_policy": "continue",
  "mappings": [
    {
      "source": "Columna CSV SKU",
      "destination": "identifiers.sku",
      "transforms": [{"name": "trim"}]
    },
    {
      "source": "Columna CSV Titulo",
      "destination": "basic_info.title"
    }
  ]
}
```

#### Campos de Destino Comunes (`destination`)

Estos son los campos donde puedes guardar información en el sistema:

-   `identifiers.sku`: SKU del producto.
-   `identifiers.upc_ean`: Código de barras.
-   `basic_info.title`: Título.
-   `basic_info.description_html`: Descripción.
-   `basic_info.brand`: Marca.
-   `pricing.cost`: Costo.
-   `variants.0.price`: Precio de venta.
-   `variants.0.inventory_quantity`: Stock.
-   `media.images.0.url`: URL de la imagen principal (usa 1, 2, etc. para más imágenes).
-   `attributes.mi_atributo`: Para guardar cualquier dato extra.

### Paso 3: Usar Transformaciones

A menudo los datos crudos necesitan limpieza. Puedes agregar una lista de `transforms` a cada mapeo.

**Transformaciones Disponibles:**

1.  **`trim`**: Elimina espacios en blanco al inicio y final.
    -   Uso: Textos, SKUs.
2.  **`upper`**: Convierte todo a MAYÚSCULAS.
    -   Uso: Códigos, Monedas.
3.  **`parse_price`**: Convierte texto con símbolos (ej. "$ 12.00") a número decimal.
    -   Uso: Precios, Costos.
4.  **`map_category`**: Traduce categorías del proveedor a las tuyas.
    -   Requiere parámetros:
        ```json
        {
          "name": "map_category",
          "params": {
            "mapping": {
              "Juguetes > Autos": "Juguetes",
              "Ropa > Hombre": "Indumentaria"
            }
          }
        }
        ```

### Paso 4: Registrar el Proveedor en el Sistema

1.  Accede al panel de administración de Django o a la aplicación `Shop Manager`.
2.  Ve a la sección de **Suppliers** (Proveedores).
3.  Crea uno nuevo.
4.  **Importante**: En el campo `Code`, ingresa exactamente el mismo nombre que usaste para el archivo JSON (sin la extensión `.json`). Ej. `mi_proveedor`.

### Paso 5: Importar y Verificar

1.  En la vista de detalle del proveedor que acabas de crear, busca la sección de "Importar Productos".
2.  Sube el archivo CSV/JSON del proveedor.
3.  El sistema procesará el archivo. Si todo sale bien, verás un mensaje de éxito con la cantidad de productos creados/actualizados.
4.  Si hay errores, el sistema te avisará (dependiendo de la política de errores). Revisa el archivo JSON y corrige los mapeos.

## 3. Ejemplo Completo

Supongamos un CSV con estas columnas: `ItemNo`, `Desc`, `WholesalePrice`.

**Configuración (`mi_proveedor.json`):**

```json
{
  "provider_id": "mi_proveedor",
  "mappings": [
    {
      "source": "ItemNo",
      "destination": "identifiers.sku",
      "transforms": [{"name": "trim"}]
    },
    {
      "source": "Desc",
      "destination": "basic_info.title"
    },
    {
      "source": "WholesalePrice",
      "destination": "pricing.cost",
      "transforms": [{"name": "parse_price"}]
    }
  ]
}
```
