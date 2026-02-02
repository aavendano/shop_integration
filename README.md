# Shop Manager & Product Sync

Sistema de gestión para sincronización de productos entre proveedores (CSV/JSON) y Shopify, utilizando Django como backend y una arquitectura ETL declarativa. Incluye gestión de precios contextuales y configuración de App de Shopify.

## Requisitos

- Python 3.8+
- Django 4.2+ (ver `requirements.txt`)
- Node.js (requerido para `shop-app`)
- Shopify CLI (para gestión de la App)

## Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone <url-del-repo>
    cd <nombre-del-repo>
    ```

2.  **Crear entorno virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate  # Windows
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de entorno**:
    Crear un archivo `.env` en la raíz (ver `shop_manager/settings.py` para lista completa):
    ```
    SECRET_KEY=tu_secret_key_django
    DEBUG=True
    SHOPIFY_CLIENT_ID=tu_client_id
    SHOPIFY_CLIENT_SECRET=tu_client_secret
    SHOPIFY_APP_SCOPES=read_products,write_products,...
    SHOPIFY_REDIRECT_URI=https://tu-dominio/accounts/shops/callback/
    API_VERSION=2024-01
    # ... otras variables
    ```

5.  **Migraciones**:
    ```bash
    python manage.py migrate
    ```

6.  **Crear superusuario**:
    ```bash
    python manage.py createsuperuser
    ```

## Ejecución

Para correr el servidor de desarrollo de Django:

```bash
python manage.py runserver
```

Acceder a `http://localhost:8000`.

Para trabajar con la App de Shopify (shop-app):

```bash
cd shop-app
npm install
npm run dev
```

## Estructura del Proyecto

-   `shop_manager/`: Configuración principal del proyecto Django.
-   `accounts/`: Gestión de usuarios y autenticación con Shopify.
-   `core/`: Utilidades generales y funciones compartidas.
-   `prices/`: Gestión de precios contextuales (Catálogos y Listas de Precios) mediante GraphQL.
-   `products_parsing/`: Motor ETL (Extract, Transform, Load) agnóstico de Django para procesar datos de proveedores.
-   `shop-app/`: Configuración de la App de Shopify (CLI), incluyendo permisos, autenticación y definición de webhooks.
-   `shopify_models/`: Modelos de Django que replican la estructura de Shopify y manejan la sincronización final.
-   `suppliers/`: Gestión de proveedores y punto de entrada para la carga de archivos de productos.
-   `docs/`: Documentación detallada del sistema.

## Documentación

Para más detalles sobre el funcionamiento y configuración:

-   [Arquitectura de Parsing](docs/PRODUCT_PARSING_ARCHITECTURE.md): Explicación del motor ETL.
-   [Manual de Integración Shopify](docs/manual_integracion_shopify.md): Configuración de autenticación, webhooks y modelos de Shopify.
-   [Onboarding Nuevos Proveedores](docs/ONBOARDING_NUEVOS_PROVEEDORES.md): Guía paso a paso para agregar nuevos proveedores y configurar sus mapeos.
