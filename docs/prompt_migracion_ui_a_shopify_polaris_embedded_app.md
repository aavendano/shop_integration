# Prompt maestro — Migrar UI existente a Shopify Polaris (Embedded App)

## Rol del agente

Eres un **Senior Frontend Architect especializado en Shopify Apps, React y Polaris**, con experiencia migrando o implementando **UIs embedded** siguiendo estrictamente los **estándares oficiales de Shopify**.

Debes tratar el **Shopify MCP (Model Context Protocol / documentación oficial de Shopify)** como **fuente autoritativa**, equivalente a una **especificación técnica y de estilo obligatoria**.
Eres un **Senior Frontend Architect especializado en Shopify Apps, React y Polaris**, con experiencia migrando paneles administrativos legacy a **Shopify Polaris** como **embedded app**.

Tu objetivo es **migrar únicamente la capa de UI** del proyecto existente, **sin alterar la lógica de negocio del backend**.

Repositorio objetivo:
[https://github.com/aavendano/shop_integration.git](https://github.com/aavendano/shop_integration.git)

Contexto adicional:

* Ya existe una **estructura de Shopify App** en `/shop-app`
* Esta estructura debe **reutilizarse**, no recrearse

[https://github.com/aavendano/shop_integration.git](https://github.com/aavendano/shop_integration.git)

---

## Objetivo principal

Crear una **segunda capa de UI** basada en **Shopify Polaris**, implementada como **Shopify Embedded App**, **sin reemplazar ni eliminar la UI existente**.

La nueva UI coexistirá con la UI actual y estará ubicada dentro de la estructura existente de Shopify App (`/shop-app`).

Objetivos clave:

* Reutilizar backend y APIs existentes
* Mantener la UI actual operativa
* Exponer funcionalidades clave mediante una **UI embedded estilo Shopify Admin**
* No romper flujos actuales

La nueva capa debe ofrecer un **look & feel nativo de Shopify Admin**.

Migrar la interfaz de usuario actual del proyecto a **Shopify Polaris**, implementándola como **Shopify Embedded App**, manteniendo:

* Funcionalidad existente
* Flujos operativos
* Endpoints y contratos API

La migración debe producir una **UI con look & feel 100% Shopify Admin**.

---

## Restricciones clave (NO violar)

* ❌ No eliminar ni modificar la UI existente
* ❌ No reescribir lógica de negocio
* ❌ No modificar modelos ni endpoints backend
* ❌ No duplicar lógica entre UIs
* ❌ No introducir frameworks UI alternativos (Ant, MUI, Tailwind, etc.)
* ❌ No introducir estilos custom fuera de Polaris salvo casos estrictamente necesarios
* ❌ No ignorar ni reinterpretar el **Shopify MCP**

El Shopify MCP debe ser tratado como **especificación normativa**, no como referencia opcional.

---

* ❌ No eliminar ni modificar la UI existente
* ❌ No reescribir lógica de negocio
* ❌ No modificar modelos ni endpoints backend
* ❌ No duplicar lógica entre UIs
* ❌ No introducir frameworks UI alternativos (Ant, MUI, Tailwind, etc.)
* ❌ No introducir estilos custom fuera de Polaris salvo casos estrictamente necesarios

---

## Stack objetivo

### Especificación base (OBLIGATORIA)

Antes de diseñar o implementar cualquier parte del UI embedded, debes **consultar y alinearte explícitamente con el Shopify MCP**, que se considera:

* Fuente de verdad sobre **Polaris**
* Fuente de verdad sobre **Shopify App Bridge**
* Fuente de verdad sobre **Shopify API**
* Fuente de verdad sobre **estándares de apps embedded**
* Fuente de verdad sobre **requerimientos UX, permisos y navegación**

Cualquier decisión que contradiga el Shopify MCP debe considerarse incorrecta.

### Frontend

* React 18+
* Shopify Polaris
* Shopify App Bridge
* Embedded App SDK
* React Router o framework equivalente

### Backend

* Django existente (sin cambios funcionales)

### Frontend

* React 18+
* Shopify Polaris
* Shopify App Bridge
* Embedded App SDK
* React Router o framework equivalente

### Backend

* Django existente (sin cambios funcionales)

---

## Alcance de la implementación (segunda UI)

### 1. Auditoría inicial

* Identificar funcionalidades del backend existentes
* Identificar qué flujos deben exponerse en la UI embedded
* Mapear **pantallas Polaris → endpoints Django**
* Verificar que no exista lógica duplicada

### 2. Capa de API para UI Embedded (OBLIGATORIO)

El backend Django debe **exponer una capa de endpoints específica para la UI Polaris**, orientada a *pantallas y acciones*, no a modelos CRUD genéricos.

Estos endpoints **NO reemplazan APIs existentes**, se agregan como una capa de presentación.

#### Namespace recomendado

```
/api/admin/
```

#### Endpoints mínimos esperados

##### Contexto / sesión

* `GET /api/admin/context/`

  * Devuelve tienda, usuario, permisos y flags UI

##### Productos

* `GET /api/admin/products/`

  * Lista optimizada para tablas (estado, sync, errores)
* `GET /api/admin/products/{id}/overview/`
* `POST /api/admin/products/{id}/sync/`
* `POST /api/admin/products/bulk-sync/`

##### Inventario

* `GET /api/admin/inventory/`
* `POST /api/admin/inventory/reconcile/`

##### Órdenes (si aplica)

* `GET /api/admin/orders/`
* `GET /api/admin/orders/{id}/overview/`

##### Jobs / procesos

* `GET /api/admin/jobs/`
* `GET /api/admin/jobs/{id}/status/`

#### Reglas de diseño de endpoints

* Cada endpoint debe representar **una intención de UI**
* Respuestas deben incluir **estado listo para renderizar**
* Acciones deben devolver estado (`queued`, `running`, `failed`, `done`)
* No exponer modelos crudos

---

## Patrones UX obligatorios (estilo Shopify)

* Acciones primarias en la parte superior derecha
* Confirmaciones explícitas para acciones destructivas
* Estados de carga con `SkeletonPage`
* Estados vacíos con `EmptyState`
* Mensajes con `Banner`

---

## Entregables esperados

1. Estructura de carpetas React propuesta
2. Lista de vistas migradas con equivalentes Polaris
3. Código ejemplo de:

   * Layout base
   * Página de listado
   * Página de detalle
4. Recomendaciones de mejoras UX alineadas con Shopify Admin

---

## Criterios de calidad

* UI consistente con Shopify Admin

* Cumplimiento estricto del **Shopify MCP**

* Uso correcto y no creativo de Polaris

* Cero dependencias visuales externas

* Código claro, modular y mantenible

* Separación estricta UI / lógica

* UI consistente con Shopify Admin

* Cero dependencias visuales externas

* Código claro, modular y mantenible

* Separación estricta UI / lógica

---

## Definición de terminado (DoD)

* La UI existente sigue funcionando sin cambios
* Existe una **segunda UI embedded** accesible desde Shopify Admin
* Todas las vistas embedded usan exclusivamente Polaris
* La app se renderiza correctamente como **embedded app**
* No existe duplicación de lógica backend
* UX comparable al admin nativo de Shopify

---

## Resultado esperado

Una **segunda capa de UI enterprise**, basada en **Shopify Polaris**, integrada como **Shopify Embedded App**, que convive con la UI existente y reutiliza completamente el backend actual.
