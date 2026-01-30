# Arquitectura de Parsing de Productos (Shopify Sync)

Este documento detalla el plan arquitectónico para la implementación de un sistema de parsing, normalización y persistencia de datos de productos provenientes de múltiples proveedores externos. El objetivo principal es desacoplar la lógica de transformación de datos del framework Django, permitiendo un sistema modular, reutilizable y configurado declarativamente.

## 1. Visión General

La arquitectura propuesta sigue un patrón ETL (Extract, Transform, Load) estricto, donde la lógica de negocio de cada proveedor se aísla en configuraciones declarativas y el sistema de persistencia (Django) actúa únicamente como un consumidor de datos ya procesados.

El sistema está diseñado para ejecutarse de manera autónoma, sin dependencias duras del ORM de Django durante las fases de extracción y transformación.

## 2. Principios Arquitectónicos

1.  **Separación Total de Capas (ETL)**: Las responsabilidades de ingestión, limpieza/normalización y guardado en base de datos están estrictamente delimitadas.
2.  **Esquema Canónico Interno**: Existe una definición de datos intermedia y estandarizada que representa un "Producto" en el contexto del negocio, independiente de la estructura de origen (proveedor) y de destino (Django/Shopify).
3.  **Configuración Declarativa (JSON)**: La lógica de mapeo y transformación para cada proveedor se define en archivos de datos (JSON), eliminando la necesidad de escribir código específico para cada nueva fuente.
4.  **Motor de Parsing Genérico**: Un único componente de software procesa las reglas definidas en los JSONs para transformar datos crudos en datos canónicos.
5.  **Persistencia como Adaptador**: La capa de Django es un adaptador final que traduce el esquema canónico a los modelos de la base de datos.

## 3. Arquitectura por Capas (ETL)

### Capa 1: Extract (Ingestión)
**Responsabilidad**: Obtener los datos crudos desde la fuente externa.
- **Entrada**: Archivos CSV, respuestas de API, XML, Scrapers.
- **Salida**: Una lista de diccionarios planos o jerárquicos (datos crudos).
- **Independencia**: Esta capa no conoce el esquema canónico ni los modelos de Django.

### Capa 2: Transform (Parsing y Normalización)
**Responsabilidad**: Convertir datos crudos en datos canónicos limpios.
- **Componente Principal**: Motor de Parsing Genérico.
- **Entrada**: Datos crudos (de la capa Extract) + Archivo de Mapeo JSON del proveedor.
- **Proceso**: Iteración, extracción de campos, aplicación de transformaciones, validación.
- **Salida**: Objetos de datos canónicos (Diccionarios o Data Classes independientes).
- **Independencia**: Totalmente agnóstico de Django. Puede ejecutarse en cualquier entorno Python.

### Capa 3: Load (Persistencia)
**Responsabilidad**: Guardar la información en la base de datos.
- **Entrada**: Datos canónicos.
- **Salida**: Registros actualizados o creados en `shopify_models`.
- **Acción**: Mapeo final de campos canónicos a campos del modelo Django, gestión de relaciones (Foreign Keys) y control de transacciones.

## 4. Esquema Canónico Interno

El Esquema Canónico es la "lengua franca" del sistema. Define qué datos son relevantes para el negocio.

**Estructura Conceptual (Resumen):**
- **Identificadores**: SKU principal, códigos de barras (UPC/EAN), MPN.
- **Información Básica**: Título normalizado, descripción (texto y HTML), marca/fabricante.
- **Precios**: Costo mayorista, MSRP, MAP, moneda.
- **Inventario**: Cantidad disponible, nombre del almacén/proveedor.
- **Clasificación**: Categoría interna, etiquetas (tags), género, tipo de producto.
- **Multimedia**: Lista de URLs de imágenes, orden de visualización.
- **Variantes**: Lista de sub-estructuras con sus propios atributos (talla, color, material) y overrides de precio/sku.
- **Atributos**: Pares clave-valor para especificaciones técnicas (peso, dimensiones, material).

Este esquema es una estructura de datos en memoria (como un diccionario tipado), no un modelo de base de datos.

## 5. Documento JSON de Mapeo por Proveedor

Cada proveedor dispone de un archivo JSON que instruye al motor cómo interpretar sus datos. Este archivo es puramente datos, sin código ejecutable.

**Componentes del JSON:**
1.  **Definición de Campos**: Una lista de reglas donde cada regla especifica:
    -   **Campo Origen**: El nombre de la clave en el dato crudo (e.g., "Product Name").
    -   **Campo Destino**: El nombre del campo en el esquema canónico (e.g., "title").
2.  **Transformaciones**: Una lista ordenada de operaciones a aplicar al valor extraído. Ejemplos conceptuales:
    -   "limpiar_espacios": Elimina espacios al inicio y final.
    -   "a_mayusculas": Convierte texto a mayúsculas.
    -   "extraer_precio": Convierte "$12.99" a el número 12.99.
    -   "mapear_categoria": Traduce la categoría del proveedor a la categoría interna usando un diccionario de equivalencias.
3.  **Valores por Defecto**: Valor a usar si el campo origen no existe o es nulo.

## 6. Motor de Parsing Genérico

El motor es una función o clase de alto nivel que orquesta el proceso.

**Flujo de Ejecución:**
1.  Carga la configuración JSON del proveedor específico.
2.  Recibe un iterador de registros crudos.
3.  Para cada registro:
    -   Inicializa una estructura canónica vacía.
    -   Recorre cada regla definida en el JSON.
    -   Extrae el valor del registro crudo usando la ruta definida (soporte para campos anidados).
    -   Aplica secuencialmente las transformaciones configuradas.
    -   Asigna el valor resultante al campo canónico correspondiente.
4.  Retorna (o genera) una lista de estructuras canónicas.

El motor maneja errores de parsing (e.g., tipos de datos incorrectos) registrándolos sin detener necesariamente todo el proceso, según la configuración de severidad.

## 7. Persistencia (Adaptador Django)

Esta es la única capa que interactúa con `shopify_models`. Actúa como un puente.

**Funciones:**
-   **Resolución de Instancias**: Busca si el producto ya existe (por SKU o identificador único) para decidir si crear o actualizar.
-   **Mapeo Final**: Asigna los valores del diccionario canónico a los atributos del modelo `Product` y `Variant` de Django.
-   **Gestión de Relaciones**:
    -   Crea o actualiza objetos `Variant` asociados al producto.
    -   Crea o actualiza objetos `Image`.
    -   Sincroniza `Metafields` si es necesario.
-   **Aislamiento**: Si los modelos de Django cambian, solo esta capa necesita ser actualizada; el parsing y los JSONs permanecen intactos.

## 8. Estrategia para Agregar Nuevos Proveedores

Para integrar un nuevo proveedor, el flujo de trabajo es:
1.  **Análisis**: Inspeccionar manualmente el archivo o API del proveedor para entender su estructura.
2.  **Configuración**: Crear un nuevo archivo JSON de mapeo.
    -   Definir qué campos del proveedor van a qué campos canónicos.
    -   Configurar las transformaciones necesarias (e.g., si el proveedor envía fechas en formato no estándar).
3.  **Validación**: Ejecutar el motor de parsing con el nuevo JSON y una muestra de datos para verificar que la salida canónica es correcta.
4.  **Despliegue**: Registrar el proveedor en el sistema (configuración) para que sea elegible en los procesos de carga.

**No se requiere programación de nuevas clases ni modificación del motor.**

## 9. Estrategia de Testing

El diseño desacoplado facilita pruebas unitarias robustas:

-   **Test de Transformaciones**: Probar funciones individuales de limpieza (input -> output) aisladas.
-   **Test de Motor**: Alimentar el motor con un JSON de prueba y un dato crudo simulado, y verificar que el diccionario canónico resultante sea exacto.
-   **Test de Configuración**: Validar que los archivos JSON de los proveedores cumplan con el esquema esperado (linting de JSON).
-   **Test de Adaptador**: Probar que, dado un diccionario canónico válido, el adaptador crea correctamente los registros en la base de datos de prueba de Django.

## 10. Beneficios y Riesgos

**Beneficios:**
-   **Mantenibilidad**: El código del núcleo cambia poco; la complejidad se mueve a la configuración.
-   **Escalabilidad**: Agregar proveedores es tarea de configuración, accesible incluso para perfiles no-dev.
-   **Robustez**: Al normalizar datos antes de tocar Django, se reduce el riesgo de ensuciar la base de datos.
-   **Portabilidad**: El motor de parsing puede reutilizarse en otros contextos o microservicios.

**Riesgos:**
-   **Complejidad de Configuración**: Los JSONs pueden volverse complejos si las transformaciones requeridas son muy lógicas o condicionales.
-   **Rendimiento**: La capa extra de abstracción y transformación en memoria puede añadir latencia comparado con una ingestión directa "hardcoded", aunque es despreciable frente a los beneficios.

## 11. Supuestos y Límites

-   Se asume que los datos de entrada pueden ser estructurados como diccionarios (JSON/Dict).
-   Transformaciones extremadamente complejas que requieran lógica de negocio dinámica (e.g., "si el precio es X y el día es martes...") podrían requerir extensiones personalizadas en las transformaciones disponibles.
