# Market and Catalog Data Model Relationships

```
┌─────────────────┐
│     Market      │
│─────────────────│
│ id              │
│ shopify_id      │
│ name            │
│ handle          │
│ enabled         │
│ primary         │
│ currency        │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐      1:1      ┌─────────────────┐
│    Catalog      │◄───────────────│  Publication    │
│─────────────────│                │─────────────────│
│ id              │                │ id              │
│ shopify_id      │                │ shopify_id      │
│ title           │                │ auto_publish    │
│ status          │                └─────────────────┘
│ market_id (FK)  │
│ publication_id  │      1:1      ┌─────────────────┐
│ price_list_id   │◄───────────────│   PriceList     │
└────────┬────────┘                │─────────────────│
         │                         │ id              │
         │ M:N                     │ shopify_id      │
         │                         │ name            │
         ▼                         │ currency        │
┌─────────────────┐                │ parent (JSON)   │
│    Product      │                └─────────────────┘
│─────────────────│
│ id              │
│ shopify_id      │
│ title           │
│ handle          │
│ description     │
│ product_type    │
│ vendor          │
│ tags            │
│ catalogs (M:N)  │
└─────────────────┘
```

## Relationships Explained

### Market → Catalog (1:N)

- A Market can have multiple Catalogs
- Each Catalog belongs to one Market (optional)
- Example: "United States" market has "US Retail Catalog" and "US Wholesale Catalog"

### Catalog → Publication (1:1)

- Each Catalog has one Publication
- Publication defines which products are available in the catalog
- When Catalog is created, Publication is auto-created if not provided

### Catalog → PriceList (1:1)

- Each Catalog has one PriceList
- PriceList defines pricing for products in the catalog
- When Catalog is created, PriceList is auto-created if not provided

### Product → Catalog (M:N)

- A Product can belong to multiple Catalogs
- A Catalog can contain multiple Products
- Managed via `product.update_catalog_availability(catalog, is_available)`
- Internally uses `publishablePublish` / `publishableUnpublish` mutations

## Data Flow

### Creating a Catalog

```
1. User creates Catalog in Django Admin
   ↓
2. Admin save_model() is called
   ↓
3. sync_catalog() is invoked
   ↓
4. If no Publication exists:
   - Create Publication locally
   - sync_publication() → Shopify
   ↓
5. If no PriceList exists:
   - Create PriceList locally
   - sync_price_list() → Shopify
   ↓
6. catalogCreate mutation → Shopify
   ↓
7. Update local Catalog with shopify_id
```

### Publishing a Product to a Catalog

```
1. product.update_catalog_availability(catalog, True)
   ↓
2. Validate catalog has Publication with shopify_id
   ↓
3. sync_product_publication(product, publication, publish=True)
   ↓
4. publishablePublish mutation → Shopify
   ↓
5. Add catalog to product.catalogs (local M:N)
```

## Shopify API Mapping

| Local Model | Shopify Object | GraphQL Type        |
| ----------- | -------------- | ------------------- |
| Market      | Market         | Market              |
| Publication | Publication    | Publication         |
| PriceList   | PriceList      | PriceList           |
| Catalog     | Catalog        | Catalog (Interface) |
| Product     | Product        | Product             |

## Key Features

1. **Automatic Dependency Creation**: When creating a Catalog, Publication and PriceList are automatically created if not provided
2. **Bi-directional Sync**: All models sync to Shopify on save via Django Admin
3. **Product Availability**: Products can be published/unpublished to/from catalogs
4. **Cascade Delete**: When a Catalog is deleted, its Publication and PriceList are also deleted (Django ORM cascade)
5. **Error Handling**: All sync operations include comprehensive error handling and user feedback
