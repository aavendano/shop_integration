# Shop Manager & Product Sync

Sistema de gestión para sincronización de productos entre proveedores (CSV/JSON) y Shopify, utilizando Django como backend y una arquitectura ETL declarativa.

## Requisitos

- Python 3.8+
- Django 4.2+ (ver `requirements.txt`)
- Node.js (opcional, para assets de frontend si se requiere modificar estilos)

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
    Crear un archivo `.env` en la raíz basado en el ejemplo (o configurar las variables manualmente):
    ```
    SECRET_KEY=tu_secret_key_django
    DEBUG=True
    SHOPIFY_API_KEY=tu_api_key
    SHOPIFY_API_SECRET=tu_api_secret
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

Para correr el servidor de desarrollo:

```bash
python manage.py runserver
```

Acceder a `http://localhost:8000`.

## Estructura del Proyecto

-   `shop_manager/`: Configuración principal del proyecto Django.
-   `accounts/`: Gestión de usuarios y autenticación con Shopify.
-   `suppliers/`: Gestión de proveedores y punto de entrada para la carga de archivos de productos.
-   `products_parsing/`: Motor ETL (Extract, Transform, Load) agnóstico de Django para procesar datos de proveedores.
-   `shopify_models/`: Modelos de Django que replican la estructura de Shopify y manejan la sincronización final.
-   `docs/`: Documentación detallada del sistema.

## Documentación

Para más detalles sobre el funcionamiento y configuración:

-   [Arquitectura de Parsing](docs/PRODUCT_PARSING_ARCHITECTURE.md): Explicación del motor ETL.
-   [Manual de Integración Shopify](docs/manual_integracion_shopify.md): Configuración de autenticación y modelos de Shopify.
-   [Onboarding Nuevos Proveedores](docs/ONBOARDING_NUEVOS_PROVEEDORES.md): Guía paso a paso para agregar nuevos proveedores y configurar sus mapeos.
