# API App for Shopify Polaris UI

This Django app provides REST API endpoints for the Shopify Polaris embedded UI.

## Structure

```
api/
├── admin/              # Admin API endpoints
│   ├── __init__.py
│   ├── urls.py        # URL routing for admin endpoints
│   └── views.py       # View classes for admin endpoints
├── middleware/         # Custom middleware
│   ├── __init__.py
│   └── session_token.py  # Session token validation middleware
├── serializers/        # DRF serializers
│   └── __init__.py
├── apps.py            # App configuration
├── tests.py           # Unit tests
└── urls.py            # Main URL routing
```

## API Endpoints

All API endpoints are namespaced under `/api/admin/`.

### Context Endpoint

**GET /api/admin/context/**

Returns context information for the Shopify Polaris UI including:
- Shop details (domain, name, currency, authentication status)
- User information (username, authentication, staff status)
- Configuration (API version, country, provider, catalog)
- Permissions (product sync, inventory management, order viewing)

Example response:
```json
{
  "shop": {
    "domain": "example.myshopify.com",
    "name": "Example Shop",
    "currency": "USD",
    "is_authenticated": true
  },
  "user": {
    "username": "admin",
    "is_authenticated": true,
    "is_staff": true
  },
  "config": {
    "api_version": "2025-10",
    "country": "US",
    "provider_code": "NALPAC",
    "catalog_name": "US-NALPAC"
  },
  "permissions": {
    "can_sync_products": true,
    "can_manage_inventory": true,
    "can_view_orders": true
  }
}
```

## Authentication

The API uses session token authentication via the `SessionTokenMiddleware`. This middleware:

1. Extracts the session token from the `Authorization` header
2. Validates the JWT token using the Shopify client secret
3. Attaches the shop to the request object
4. Returns 401 for invalid or expired tokens

### Token Format

```
Authorization: Bearer <jwt_token>
```

The JWT token should be obtained from Shopify App Bridge and include:
- `dest`: Shop domain
- `aud`: Shopify client ID
- Signature validated with Shopify client secret

## Configuration

The API is configured in `shop_manager/settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}
```

## Testing

Run tests with:
```bash
python manage.py test api
```

## Future Endpoints

The following endpoints are planned for future implementation:

- **Products**: List, overview, sync, bulk sync
- **Inventory**: List, reconcile
- **Orders**: List, overview
- **Jobs**: List, status tracking
