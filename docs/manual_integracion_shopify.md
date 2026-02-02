# Manual de Integración con Shopify

Este documento describe cómo el proyecto gestiona la autenticación, configuración y sincronización con Shopify.

## 1. Arquitectura de la App (`shop-app` vs `shop_manager`)

El proyecto utiliza una estructura híbrida:

1.  **`shop-app` (Shopify CLI)**: Define la configuración de la aplicación ante Shopify.
    -   Archivo: `shop-app/shopify.app.toml`
    -   Responsabilidad: Definir Scopes, URLs de redirección y **Webhooks**.
2.  **`shop_manager` (Django)**: Backend que procesa la lógica de negocio y persiste los datos.
    -   Apps: `accounts`, `shopify_models`, `prices`.
    -   Responsabilidad: Autenticación OAuth, gestión de base de datos, parsing de productos y precios contextuales.

## 2. Autenticación (`accounts`)

La aplicación `accounts` maneja el flujo OAuth y almacena las credenciales.

### Flujo de Conexión

1.  La configuración en `shop-app/shopify.app.toml` define la URL de redirección hacia Django:
    ```toml
    [auth]
    redirect_urls = [ "https://<tu-dominio>/accounts/shops/callback/" ]
    ```
2.  El usuario inicia el proceso desde Django (`/accounts/shops/`).
3.  Shopify solicita permisos basados en los scopes definidos en la App.
4.  Shopify redirige a `/accounts/shops/callback/`.
5.  Django intercambia el código por un token de acceso permanente (Offline Access) y crea una `Session`.

## 3. Webhooks

A diferencia de versiones anteriores donde los webhooks se gestionaban internamente en Django, la configuración actual delega esta responsabilidad.

-   **Definición**: Los webhooks se declaran en `shop-app/shopify.app.toml`.
-   **Destino Actual**: Actualmente están configurados para enviar los eventos a un servicio externo (n8n), no directamente a la aplicación Django.
-   **Código Legacy**: Existe un archivo `shopify_models/handlers.py` con lógica para procesar webhooks, pero **no se utiliza en tiempo de ejecución** bajo la configuración actual de `shop-app`, ya que los webhooks no apuntan a este backend.

## 4. Modelos de Datos (`shopify_models` y `prices`)

-   **`shopify_models`**: Replica la estructura de productos y variantes de Shopify. Se alimenta principalmente del motor de parsing (`products_parsing`).
-   **`prices`**: Gestiona **Precios Contextuales** usando la API GraphQL de Shopify. Permite crear Catálogos y Listas de Precios específicas por país/proveedor, interactuando directamente con la API de Shopify usando las sesiones almacenadas.

## 5. Configuración Requerida

En `settings.py` (y `.env`), se deben definir las variables que coincidan con la configuración de Shopify Partners:

-   `SHOPIFY_CLIENT_ID`: Client ID de la App.
-   `SHOPIFY_CLIENT_SECRET`: Client Secret.
-   `SHOPIFY_APP_SCOPES`: Scopes (ej. `read_products,write_products`).
-   `SHOPIFY_REDIRECT_URI`: URL completa del callback.
-   `API_VERSION`: Versión de la API (ej. `2024-01`).

## 6. Uso en Desarrollo

1.  **Túnel**: Usar `ngrok` o Cloudflare Tunnel para exponer localhost.
2.  **Actualizar URLs**:
    -   En `.env`: `SHOPIFY_REDIRECT_URI`, `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`.
    -   En `shop-app/shopify.app.toml`: `application_url` y `redirect_urls`.
3.  **Desplegar Configuración**:
    Si se cambia `shopify.app.toml`, ejecutar `shopify app deploy` (o `dev`) desde la carpeta `shop-app` para actualizar la configuración en Shopify.
