# Manual de Integración con Shopify

Este documento describe cómo el proyecto gestiona la autenticación y sincronización con Shopify a través de las aplicaciones `accounts` y `shopify_models`.

## 1. Autenticación (`accounts`)

La aplicación `accounts` maneja la conexión con las tiendas Shopify. A diferencia de implementaciones anteriores, ahora utiliza modelos propios para gestionar la sesión.

### Modelos Principales

-   **`Shop`**: Representa una tienda Shopify instalada.
    -   `myshopify_domain`: Dominio único (ej. `mi-tienda.myshopify.com`).
    -   `is_authentified`: Estado de la conexión.
    -   Credenciales OAuth (`client_id`, `client_secret`).

-   **`Session`**: Almacena el token de acceso válido.
    -   `shop`: Relación 1:1 con el modelo `Shop`.
    -   `token`: El *access token* obtenido de Shopify (Offline access).
    -   `site`: URL completa del sitio para la API.

### Flujo de Conexión

1.  El usuario accede a la lista de tiendas en `/accounts/shops/`.
2.  Agrega una nueva tienda o selecciona "Autenticar" en una existente.
3.  El sistema redirige a Shopify para solicitar permisos (OAuth).
4.  Al confirmar, Shopify redirige de vuelta al *callback* (`/accounts/shops/callback/`).
5.  Se crea o actualiza el registro `Session` con el token permanente.

## 2. Modelos de Datos (`shopify_models`)

Esta aplicación contiene los modelos de Django que replican la estructura de recursos de Shopify (Productos, Variantes, Imágenes).

### Sincronización

La sincronización se realiza principalmente a través de la importación de proveedores (`suppliers` + `products_parsing`), la cual:

1.  Parsea el archivo del proveedor.
2.  Genera objetos canónicos.
3.  Usa el adaptador de Django (`products_parsing/adapters/django_adapter.py`) para guardar en `shopify_models`.

*Nota: La sincronización inversa (descargar de Shopify a Django) o vía Webhooks no está activada por defecto en la configuración actual, aunque los handlers existen en `handlers.py`.*

## 3. Configuración Requerida

En `settings.py` (o variables de entorno), se deben definir:

-   `SHOPIFY_CLIENT_ID`: API Key de la App en Shopify Partners.
-   `SHOPIFY_CLIENT_SECRET`: API Secret Key.
-   `SHOPIFY_APP_SCOPES`: Permisos requeridos (ej. `read_products,write_products`).
-   `SHOPIFY_REDIRECT_URI`: URL de callback (debe coincidir con la configurada en el Partner Dashboard).
-   `API_VERSION`: Versión de la API de Shopify (ej. `2024-01`).

## 4. Uso en Desarrollo

Para probar la integración localmente:

1.  Asegúrate de usar un túnel HTTPS (como `ngrok`) si necesitas recibir callbacks de Shopify.
2.  Configura `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con tu dominio de túnel.
3.  Registra la URL de redirección en tu App de Shopify: `https://<tu-dominio>/accounts/shops/callback/`.
