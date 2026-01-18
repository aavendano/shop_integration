# Manual de usuario: apps Django `shopify_sync`, `shopify_auth` y `shopify_webhook`

Este documento describe las capacidades, el onboarding y la configuración obligatoria/opcional para integrar las apps Django del proyecto: `shopify_sync`, `shopify_auth` y `shopify_webhook`. Está pensado para que puedas configurar el proyecto desde cero y empezar el desarrollo sin depender de otras fuentes.

## Requisitos previos

- Python 3.x y Django 4.2+ (según el README del paquete).【F:README.md†L12-L12】
- Acceso al panel de administración de Shopify y una app privada/pública con:
  - `SHOPIFY_APP_API_KEY`
  - `SHOPIFY_APP_API_SECRET`
  - Alcances (`SHOPIFY_APP_API_SCOPE`)
  - Versión de API (`SHOPIFY_APP_API_VERSION`)

## Mapa rápido de capacidades

### `shopify_auth`

**¿Qué hace?**
- Implementa un flujo OAuth clásico con vistas de `login`, `authenticate` y `finalize` para autenticar tiendas Shopify y obtener tokens de acceso.【F:shopify_auth/urls.py†L1-L7】【F:shopify_auth/views.py†L19-L83】
- Expone un *context processor* para inyectar `SHOPIFY_APP_NAME`, `SHOPIFY_APP_API_KEY` y `SHOPIFY_APP_DEV_MODE` en plantillas.【F:shopify_auth/context_processors.py†L1-L9】
- Incluye un backend de autenticación (`ShopUserBackend`) para persistir el token del usuario autenticado.【F:shopify_auth/backends.py†L1-L15】
- Incluye `AbstractShopUser` para construir un usuario asociado a `myshopify_domain` y `token`, además de sesiones Shopify temporales.【F:shopify_auth/models.py†L30-L69】
- Posee un *check* que valida `SHOPIFY_AUTH_BOUNCE_PAGE_URL` en settings.【F:shopify_auth/checks.py†L1-L24】

### `shopify_webhook`

**¿Qué hace?**
- Provee un `WebhookView` para recibir webhooks con verificación de HMAC, y dispara señales genéricas y específicas por tópico (`orders_create`, `products_update`, etc.).【F:shopify_webhook/views.py†L10-L39】【F:shopify_webhook/signals.py†L1-L45】
- Ofrece decoradores para validar webhooks (`@webhook`), peticiones de Carrier Services (`@carrier_request`) y App Proxy (`@app_proxy`).【F:shopify_webhook/decorators.py†L14-L100】
- Incluye utilidades para cálculo de HMAC y firma de App Proxy; permite desactivar validación de App Proxy con `SKIP_APP_PROXY_VALIDATION` (por defecto respeta `DEBUG`).【F:shopify_webhook/helpers.py†L13-L64】

### `shopify_sync`

**¿Qué hace?**
- Sincroniza recursos de Shopify con modelos locales mediante `ShopifyResourceManager` y métodos `sync_one`, `sync_many`, `sync_all` (entre otros).【F:shopify_sync/models/base.py†L54-L214】
- Usa un modelo `Session` que contiene el token y el sitio Shopify, y lo convierte en sesiones del SDK de Shopify para activar peticiones autenticadas.【F:shopify_sync/models/session.py†L8-L65】
- Escucha la señal genérica `webhook_received` de `shopify_webhook` y sincroniza automáticamente cuando llegan webhooks válidos.【F:shopify_sync/apps.py†L1-L24】【F:shopify_sync/handlers.py†L1-L63】

## Onboarding paso a paso

### 1) Instalar dependencias y añadir apps

Agrega las apps a `INSTALLED_APPS` en tu proyecto. En este repositorio ya están incluidas en `shop_manager/settings.py` como ejemplo.【F:shop_manager/settings.py†L33-L56】

```python
INSTALLED_APPS = [
    ...
    'shopify_sync',
    'shopify_auth',
    'shopify_webhook',
]
```

### 2) Configurar variables de entorno y settings base

Define los valores requeridos por Shopify Auth en tus settings (o mediante variables de entorno). Ejemplo basado en `shop_manager/settings.py`:【F:shop_manager/settings.py†L112-L140】

```python
SHOPIFY_APP_NAME = 'shop-manager'
SHOPIFY_APP_API_KEY = os.environ.get('SHOPIFY_APP_API_KEY')
SHOPIFY_APP_API_SECRET = os.environ.get('SHOPIFY_APP_API_SECRET')
SHOPIFY_APP_API_SCOPE = ['read_products', 'read_orders']
SHOPIFY_APP_API_VERSION = os.environ.get('API_VERSION')
SHOPIFY_APP_DEV_MODE = True
LOGIN_REDIRECT_URL = '/'
SHOPIFY_AUTH_BOUNCE_PAGE_URL = LOGIN_REDIRECT_URL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

> **Nota:** `SHOPIFY_AUTH_BOUNCE_PAGE_URL` es obligatorio. Si falta o está vacío, el check de `shopify_auth` fallará.【F:shopify_auth/checks.py†L1-L24】

### 3) Configurar el usuario Shopify (recomendado)

Para aprovechar el backend de autenticación Shopify, se recomienda que tu `AUTH_USER_MODEL` herede de `AbstractShopUser`, que provee `myshopify_domain` y `token` además de la propiedad `session`.【F:shopify_auth/models.py†L30-L69】

```python
# tu_app/models.py
from shopify_auth.models import AbstractShopUser

class AuthAppShopUser(AbstractShopUser):
    pass
```

En settings:

```python
AUTH_USER_MODEL = 'tu_app.AuthAppShopUser'
```

Y registra el backend si quieres usar la autenticación con token guardado:

```python
AUTHENTICATION_BACKENDS = (
    'shopify_auth.backends.ShopUserBackend',
)
```

> Si ya tienes un `AUTH_USER_MODEL` distinto, evalúa si necesitas extenderlo o usar un modelo separado según tu arquitectura. En este repositorio, el usuario por defecto es `accounts.User`.【F:shop_manager/settings.py†L146-L149】【F:accounts/models.py†L1-L8】

### 4) Configurar URLs

#### `shopify_auth`

Incluye las URLs para login/autenticación:

```python
from django.urls import include, path

urlpatterns = [
    path('auth/', include('shopify_auth.urls')),
]
```

Las vistas disponibles son:
- `/auth/` → login (renderiza template si falta `shop`).【F:shopify_auth/views.py†L19-L44】
- `/auth/authenticate/` → redirige a Shopify para OAuth.【F:shopify_auth/views.py†L47-L71】
- `/auth/finalize/` → intercambia `code` por token y autentica usuario.【F:shopify_auth/views.py†L74-L83】

#### `shopify_webhook`

Agrega un endpoint para recibir webhooks:

```python
from django.urls import path
from shopify_webhook.views import WebhookView

urlpatterns = [
    path('webhooks/', WebhookView.as_view(), name='shopify_webhook'),
]
```

### 5) Migraciones y base de datos

Ejecuta las migraciones necesarias:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6) Crear la sesión Shopify para `shopify_sync`

`shopify_sync` utiliza un modelo `Session` con `token` y `site`. Este `site` debe ser el dominio tipo `mi-tienda.myshopify.com`, y el `token` corresponde al **Admin API access token** que Shopify entrega en el flujo OAuth (o en desarrollo local).【F:shopify_sync/models/session.py†L8-L25】

Crea la sesión desde el admin de Django o vía shell:

```python
from shopify_sync.models import Session

Session.objects.create(
    token='shpat_...',
    site='mi-tienda.myshopify.com',
)
```

### 7) Sincronización inicial y desarrollo

Con una `Session` creada, puedes sincronizar recursos:

```python
from shopify_sync.models import Product, Session
session = Session.objects.first()
products = Product.objects.sync_all(session, query='bar')
```

También puedes modificar un recurso local y subirlo con `push=True` al guardar, o sincronizar cambios de Shopify con `sync()`.【F:README.md†L21-L47】

## Configuraciones obligatorias y opcionales

### `shopify_auth`

**Obligatorias**
- `SHOPIFY_APP_NAME` (nombre visible en UI de login).【F:shopify_auth/context_processors.py†L1-L9】
- `SHOPIFY_APP_API_KEY` y `SHOPIFY_APP_API_SECRET` (OAuth y validación).【F:shop_manager/settings.py†L112-L118】
- `SHOPIFY_APP_API_SCOPE` (permisos).【F:shop_manager/settings.py†L119-L119】
- `SHOPIFY_APP_API_VERSION` (versión de Shopify API).【F:shop_manager/settings.py†L121-L121】
- `SHOPIFY_AUTH_BOUNCE_PAGE_URL` (obligatorio según el check).【F:shopify_auth/checks.py†L1-L24】
- `LOGIN_REDIRECT_URL` (destino tras login).【F:shop_manager/settings.py†L152-L154】

**Opcionales**
- `SHOPIFY_APP_DEV_MODE`: en `True`, `authenticate` omite OAuth y usa token fijo (`000...`). Ideal para desarrollo local.【F:shopify_auth/views.py†L47-L59】
- `SECURE_PROXY_SSL_HEADER`: recomendado si usas proxy o túneles SSL.【F:shop_manager/settings.py†L155-L160】
- `AUTHENTICATION_BACKENDS`: si usas `ShopUserBackend` para persistir token de Shopify.【F:shopify_auth/backends.py†L1-L15】

### `shopify_webhook`

**Obligatorias**
- `SHOPIFY_APP_API_SECRET` (para validar HMAC de webhooks y firmas).【F:shopify_webhook/decorators.py†L33-L60】【F:shopify_webhook/helpers.py†L13-L31】

**Opcionales**
- `SKIP_APP_PROXY_VALIDATION`: si está activo, deshabilita validación de firma de App Proxy (default sigue `DEBUG`).【F:shopify_webhook/helpers.py†L43-L64】
- `LIQUID_TEMPLATE_CONTENT_TYPE`: sobrescribe el content-type para `LiquidTemplateView` (default `application/liquid; charset=utf-8`).【F:shopify_webhook/views.py†L41-L55】

### `shopify_sync`

**Obligatorias**
- Al menos una entrada en `shopify_sync.Session` con `token` y `site`.【F:shopify_sync/models/session.py†L8-L25】
- `SHOPIFY_APP_API_VERSION` para construir sesiones de Shopify (aplica también a `shopify_auth`).【F:shopify_sync/models/session.py†L6-L12】

**Opcionales**
- `SHOPIFY_API_PAGE_LIMIT` (default 250) puede ajustarse en `shopify_sync.__init__` si necesitas paginación distinta.【F:shopify_sync/__init__.py†L1-L3】

## Flujo recomendado de desarrollo

1. Configura settings y variables de entorno (clave/secret, scopes, API version, etc.).【F:shop_manager/settings.py†L112-L140】
2. Ejecuta migraciones.
3. Crea una `Session` en `shopify_sync`.
4. Accede a `/auth/` con `shop=tu-tienda.myshopify.com` para iniciar OAuth y guardar el token del usuario Shopify.【F:shopify_auth/views.py†L19-L83】
5. Configura webhooks en Shopify para apuntar a tu endpoint `/webhooks/`. `shopify_webhook` validará HMAC y disparará señales; `shopify_sync` escuchará `webhook_received` para sincronizar modelos automáticamente.【F:shopify_webhook/views.py†L10-L39】【F:shopify_sync/apps.py†L1-L24】【F:shopify_sync/handlers.py†L1-L63】
6. Usa `sync_all` y `save(push=True)` para sincronizaciones manuales cuando lo necesites.【F:README.md†L21-L47】

## Notas útiles

- Si usas apps embebidas y sesión basada en tokens, existe un submódulo `shopify_auth.session_tokens` con instrucciones en su README, incluyendo middleware y autenticación para Django REST Framework. Revisalo si tu implementación lo requiere.【F:shopify_auth/session_tokens/README.md†L1-L118】
- `shopify_webhook` también soporta App Proxy y Carrier Service requests vía decoradores; si vas a usarlos, revisa sus validaciones en `decorators.py`.【F:shopify_webhook/decorators.py†L14-L100】
