# Remix Frontend Infrastructure Setup

This document describes the infrastructure setup for the Shopify Polaris UI Migration frontend application.

## Project Structure

```
app/
├── types/                    # TypeScript type definitions
│   ├── api.ts               # Core API response types
│   ├── products.ts          # Product-related types
│   ├── inventory.ts         # Inventory-related types
│   └── jobs.ts              # Job-related types
├── services/                # API client services
│   ├── api.ts               # Base API client
│   ├── context.ts           # Context/session service
│   ├── products.ts          # Products API service
│   ├── inventory.ts         # Inventory API service
│   └── jobs.ts              # Jobs API service
├── utils/                   # Utility functions
│   └── errors.ts            # Error handling utilities
├── components/              # Reusable Polaris components
├── routes/                  # Remix routes
├── root.jsx                 # Root layout
├── shopify.server.js        # Shopify App Bridge configuration
└── db.server.js             # Database configuration
```

## Technology Stack

- **Framework**: Remix 2.16+ with React 18.2+
- **UI Components**: Shopify Polaris 12.0+
- **Integration**: Shopify App Bridge 4.1+
- **Language**: TypeScript 5.2+
- **Build Tool**: Vite 6.2+
- **Database**: Prisma with SQLite (dev) / PostgreSQL (prod)

## Type System

All API responses are fully typed using TypeScript interfaces:

### Core Types (`app/types/api.ts`)
- `PaginatedResponse<T>` - Paginated list responses
- `ApiError` - Error response structure
- `ShopContext` - Shop and user context

### Domain Types
- **Products** (`app/types/products.ts`): Product, Variant, Image types
- **Inventory** (`app/types/inventory.ts`): Inventory item and reconciliation types
- **Jobs** (`app/types/jobs.ts`): Job status and detail types

## API Client Services

All services extend the base `ApiClient` class and provide type-safe methods:

### Base Client (`app/services/api.ts`)
```typescript
const client = new ApiClient(baseUrl, sessionToken);
const data = await client.get<T>(endpoint);
const result = await client.post<T>(endpoint, data);
```

### Service Classes
- **ContextService**: Retrieve shop context and user info
- **ProductsService**: List, get, sync, and bulk sync products
- **InventoryService**: List inventory and reconcile quantities
- **JobsService**: List and get job details

## Error Handling

The `app/utils/errors.ts` module provides utilities for consistent error handling:

- `getErrorMessage(error)` - Extract user-friendly message
- `getFieldErrors(error)` - Extract validation errors
- `isNetworkError(error)` - Detect network errors
- `logError(error, context)` - Log errors with context
- `formatErrorForDisplay(error)` - Format for UI display

## Environment Configuration

### Development
```env
DATABASE_URL="file:dev.sqlite"
DJANGO_API_URL="http://localhost:8000"
```

### Production
```env
DATABASE_URL="postgresql://..."
DJANGO_API_URL="https://api.example.com"
```

## Authentication Flow

1. User accesses embedded app in Shopify Admin
2. Shopify App Bridge authenticates and provides session token
3. Session token included in `Authorization: Bearer <token>` header
4. Django backend validates token and returns render-ready data
5. Remix routes use session token to create API client

## API Integration Pattern

### In Remix Loaders
```typescript
export const loader = async ({ request }) => {
  const { session } = await authenticate.admin(request);
  const api = await createApiClient(request, session.accessToken);
  const service = new ProductsService(api);
  const products = await service.list({ page: 1 });
  return json(products);
};
```

### In Components
```typescript
const { products } = useLoaderData<typeof loader>();
// Use products directly - already typed and render-ready
```

## Polaris Component Usage

All UI components use exclusively Shopify Polaris:
- Layout components: `Page`, `Layout`, `Card`
- Data display: `IndexTable`, `DataTable`, `Badge`
- Forms: `TextField`, `Select`, `ChoiceList`
- Feedback: `Banner`, `Toast`, `Modal`
- Loading: `SkeletonPage`, `SkeletonBodyText`, `Spinner`

## Build and Development

### Development Server
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run start
```

### Type Checking
```bash
npx tsc --noEmit
```

### Linting
```bash
npm run lint
```

## Next Steps

1. Implement API client services in route loaders
2. Create Polaris components for each view
3. Set up App Bridge integration for navigation and toasts
4. Implement error handling and loading states
5. Add property-based tests for API integration
