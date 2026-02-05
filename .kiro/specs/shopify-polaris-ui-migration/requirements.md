# Requirements Document

## Introduction

This document specifies the requirements for migrating the existing Django-based Shop Manager UI to a Shopify Polaris Embedded App. The migration creates a second UI layer that coexists with the current Django UI, providing a native Shopify Admin experience for shop owners while maintaining all existing backend functionality unchanged.

The system will provide embedded views for Products, Inventory, Orders, Jobs, and Settings management, accessible directly from the Shopify Admin interface. All views will use exclusively Shopify Polaris components to ensure visual and functional consistency with the Shopify Admin ecosystem.

## Glossary

- **Embedded_App**: A Shopify application that runs within an iframe inside the Shopify Admin interface
- **Polaris**: Shopify's design system and React component library for building admin interfaces
- **App_Bridge**: Shopify's JavaScript library for communication between embedded apps and the Shopify Admin
- **Django_Backend**: The existing Django application containing Shop, Session, Product, Inventory, Orders, and Prices management
- **Remix_Frontend**: The React-based frontend application using Remix framework
- **API_Layer**: Django REST Framework endpoints under `/api/admin/` namespace
- **Session_Token**: JWT token used for authenticating requests between Remix and Django
- **Context_Endpoint**: API endpoint providing shop info, user data, and permissions
- **Sync_Action**: Operation that synchronizes local product data with Shopify
- **Bulk_Action**: Operation performed on multiple items simultaneously
- **Render_Ready_State**: Data formatted for direct consumption by UI components without additional processing
- **Shopify_MCP**: Model Context Protocol specification for Shopify integration patterns

## Requirements

### Requirement 1: Backend API Layer

**User Story:** As a frontend developer, I want REST API endpoints that provide render-ready data, so that I can build UI views without duplicating backend logic.

#### Acceptance Criteria

1. THE API_Layer SHALL expose all endpoints under the `/api/admin/` namespace
2. WHEN a request is made to any API endpoint, THE API_Layer SHALL authenticate using Session_Token
3. WHEN authentication fails, THE API_Layer SHALL return HTTP 401 with error details
4. THE API_Layer SHALL return Render_Ready_State for all endpoints
5. THE API_Layer SHALL NOT expose raw CRUD operations
6. THE API_Layer SHALL use Django REST Framework serializers for data transformation
7. WHEN an error occurs, THE API_Layer SHALL return structured error responses with HTTP status codes

### Requirement 2: Context and Session Management

**User Story:** As an embedded app, I want to retrieve shop context and session information, so that I can display relevant data and maintain authentication.

#### Acceptance Criteria

1. THE API_Layer SHALL provide a `/api/admin/context/` endpoint
2. WHEN the context endpoint is called, THE API_Layer SHALL return shop information including myshopify_domain, name, and currency
3. WHEN the context endpoint is called, THE API_Layer SHALL return user information if available
4. WHEN the context endpoint is called, THE API_Layer SHALL return permission flags for available features
5. WHEN no active session exists, THE Context_Endpoint SHALL return HTTP 404 with descriptive message
6. THE Context_Endpoint SHALL complete within 500ms under normal conditions

### Requirement 3: Products API

**User Story:** As a shop manager, I want to view and manage products through the embedded app, so that I can maintain my catalog without leaving Shopify Admin.

#### Acceptance Criteria

1. THE API_Layer SHALL provide a `/api/admin/products/` endpoint for listing products
2. WHEN listing products, THE API_Layer SHALL support pagination with configurable page size
3. WHEN listing products, THE API_Layer SHALL support filtering by title, vendor, product_type, and tags
4. WHEN listing products, THE API_Layer SHALL support sorting by created_at, updated_at, and title
5. WHEN listing products, THE API_Layer SHALL return product data including id, title, vendor, product_type, tags, variant count, and sync status
6. THE API_Layer SHALL provide a `/api/admin/products/{id}/` endpoint for product details
7. WHEN retrieving product details, THE API_Layer SHALL return complete product information including variants, images, and inventory data
8. THE API_Layer SHALL provide a `/api/admin/products/{id}/sync/` endpoint for synchronizing a single product
9. WHEN a sync request is made, THE API_Layer SHALL invoke the existing export_to_shopify method
10. WHEN sync completes successfully, THE API_Layer SHALL return HTTP 200 with sync results
11. WHEN sync fails, THE API_Layer SHALL return HTTP 500 with error details
12. THE API_Layer SHALL provide a `/api/admin/products/bulk-sync/` endpoint for synchronizing multiple products
13. WHEN bulk sync is requested, THE API_Layer SHALL accept an array of product IDs
14. WHEN bulk sync executes, THE API_Layer SHALL process each product and return aggregated results

### Requirement 4: Inventory API

**User Story:** As a shop manager, I want to view and reconcile inventory through the embedded app, so that I can maintain accurate stock levels.

#### Acceptance Criteria

1. THE API_Layer SHALL provide a `/api/admin/inventory/` endpoint for listing inventory items
2. WHEN listing inventory, THE API_Layer SHALL return data for all variants with inventory tracking enabled
3. WHEN listing inventory, THE API_Layer SHALL include product title, variant title, SKU, source_quantity, and sync status
4. WHEN listing inventory, THE API_Layer SHALL support filtering by product title and SKU
5. THE API_Layer SHALL provide a `/api/admin/inventory/reconcile/` endpoint for inventory reconciliation
6. WHEN reconciliation is requested, THE API_Layer SHALL synchronize inventory quantities with Shopify
7. WHEN reconciliation completes, THE API_Layer SHALL return HTTP 200 with reconciliation results

### Requirement 5: Orders API

**User Story:** As a shop manager, I want to view orders through the embedded app, so that I can monitor sales and fulfillment.

#### Acceptance Criteria

1. WHERE order management is enabled, THE API_Layer SHALL provide a `/api/admin/orders/` endpoint
2. WHEN listing orders, THE API_Layer SHALL return order data including order number, customer, total, status, and created date
3. WHEN listing orders, THE API_Layer SHALL support pagination
4. WHEN listing orders, THE API_Layer SHALL support filtering by status and date range
5. WHERE order management is enabled, THE API_Layer SHALL provide a `/api/admin/orders/{id}/` endpoint
6. WHEN retrieving order details, THE API_Layer SHALL return complete order information including line items and fulfillment status

### Requirement 6: Jobs and Background Processes API

**User Story:** As a shop manager, I want to monitor background jobs and processes, so that I can track long-running operations.

#### Acceptance Criteria

1. THE API_Layer SHALL provide a `/api/admin/jobs/` endpoint for listing background jobs
2. WHEN listing jobs, THE API_Layer SHALL return job data including job type, status, progress, started_at, and completed_at
3. WHEN listing jobs, THE API_Layer SHALL support filtering by status and job type
4. THE API_Layer SHALL provide a `/api/admin/jobs/{id}/` endpoint for job details
5. WHEN retrieving job details, THE API_Layer SHALL return complete job information including logs and error messages if applicable

### Requirement 7: Polaris Dashboard View

**User Story:** As a shop manager, I want to see a dashboard with key metrics when I open the app, so that I can quickly understand my shop's status.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a dashboard route at `/app`
2. WHEN the dashboard loads, THE Remix_Frontend SHALL display key metrics using Polaris Layout and Card components
3. THE Remix_Frontend SHALL display total product count
4. THE Remix_Frontend SHALL display products pending sync count
5. THE Remix_Frontend SHALL display inventory items count
6. THE Remix_Frontend SHALL display recent jobs status
7. WHEN metrics are loading, THE Remix_Frontend SHALL display SkeletonPage component
8. WHEN an error occurs loading metrics, THE Remix_Frontend SHALL display Banner component with error message

### Requirement 8: Polaris Products List View

**User Story:** As a shop manager, I want to browse and manage products in a list view, so that I can efficiently work with my catalog.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a products list route at `/app/products`
2. WHEN the products list loads, THE Remix_Frontend SHALL display products using Polaris IndexTable component
3. THE Remix_Frontend SHALL display columns for product image, title, vendor, type, variant count, and sync status
4. WHEN products are loading, THE Remix_Frontend SHALL display SkeletonPage with SkeletonBodyText
5. WHEN no products exist, THE Remix_Frontend SHALL display EmptyState component with illustration and action button
6. THE Remix_Frontend SHALL provide filters using Polaris Filters component for title, vendor, product_type, and tags
7. THE Remix_Frontend SHALL provide sorting options for created date, updated date, and title
8. THE Remix_Frontend SHALL provide pagination using Polaris Pagination component
9. THE Remix_Frontend SHALL provide bulk actions for sync and export operations
10. WHEN a bulk action is selected, THE Remix_Frontend SHALL display confirmation modal using Polaris Modal component
11. WHEN bulk action completes, THE Remix_Frontend SHALL display Toast notification with results

### Requirement 9: Polaris Product Detail View

**User Story:** As a shop manager, I want to view detailed product information, so that I can review and manage individual products.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a product detail route at `/app/products/{id}`
2. WHEN product detail loads, THE Remix_Frontend SHALL display product information using Polaris Layout and Card components
3. THE Remix_Frontend SHALL display product title, description, vendor, type, and tags
4. THE Remix_Frontend SHALL display product images using Polaris Thumbnail component
5. THE Remix_Frontend SHALL display variants table using Polaris DataTable component
6. THE Remix_Frontend SHALL display variant columns for title, SKU, price, inventory, and sync status
7. THE Remix_Frontend SHALL provide a sync button using Polaris Button component
8. WHEN sync button is clicked, THE Remix_Frontend SHALL call the sync API endpoint
9. WHEN sync is in progress, THE Remix_Frontend SHALL disable the button and show loading state
10. WHEN sync completes, THE Remix_Frontend SHALL display Toast notification with result
11. WHEN product is loading, THE Remix_Frontend SHALL display SkeletonPage component
12. WHEN product is not found, THE Remix_Frontend SHALL display EmptyState with navigation back to list

### Requirement 10: Polaris Inventory View

**User Story:** As a shop manager, I want to view and reconcile inventory, so that I can maintain accurate stock levels.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide an inventory route at `/app/inventory`
2. WHEN inventory view loads, THE Remix_Frontend SHALL display inventory items using Polaris IndexTable component
3. THE Remix_Frontend SHALL display columns for product, variant, SKU, quantity, and sync status
4. THE Remix_Frontend SHALL provide filters using Polaris Filters component for product title and SKU
5. THE Remix_Frontend SHALL provide a reconcile action button using Polaris Button component
6. WHEN reconcile is clicked, THE Remix_Frontend SHALL call the reconcile API endpoint
7. WHEN reconciliation completes, THE Remix_Frontend SHALL display Toast notification with results
8. WHEN inventory is loading, THE Remix_Frontend SHALL display SkeletonPage component

### Requirement 11: Polaris Jobs View

**User Story:** As a shop manager, I want to monitor background jobs, so that I can track long-running operations.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a jobs route at `/app/jobs`
2. WHEN jobs view loads, THE Remix_Frontend SHALL display jobs using Polaris IndexTable component
3. THE Remix_Frontend SHALL display columns for job type, status, progress, started time, and duration
4. THE Remix_Frontend SHALL use Polaris Badge component to display job status
5. THE Remix_Frontend SHALL use Polaris ProgressBar component to display job progress
6. THE Remix_Frontend SHALL provide filters for job status and type
7. WHEN a job row is clicked, THE Remix_Frontend SHALL navigate to job detail view
8. THE Remix_Frontend SHALL auto-refresh job list every 5 seconds when active jobs exist
9. WHEN jobs are loading, THE Remix_Frontend SHALL display SkeletonPage component

### Requirement 12: Polaris Settings View

**User Story:** As a shop manager, I want to configure app settings, so that I can customize behavior for my shop.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a settings route at `/app/settings`
2. WHEN settings view loads, THE Remix_Frontend SHALL display settings using Polaris Layout and Card components
3. THE Remix_Frontend SHALL display shop information including name, domain, and currency
4. THE Remix_Frontend SHALL display pricing configuration status
5. THE Remix_Frontend SHALL display sync preferences using Polaris ChoiceList component
6. THE Remix_Frontend SHALL provide a save button using Polaris Button component
7. WHEN save is clicked, THE Remix_Frontend SHALL validate and submit settings
8. WHEN save completes, THE Remix_Frontend SHALL display Toast notification

### Requirement 13: App Bridge Integration

**User Story:** As an embedded app, I want to integrate with Shopify Admin using App Bridge, so that I provide a seamless native experience.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL initialize App_Bridge on application load
2. THE Remix_Frontend SHALL use App_Bridge for navigation within the embedded app
3. THE Remix_Frontend SHALL use App_Bridge Toast for notifications
4. THE Remix_Frontend SHALL use App_Bridge TitleBar for page titles and actions
5. WHEN navigation occurs, THE Remix_Frontend SHALL update the browser URL using App_Bridge
6. WHEN external links are needed, THE Remix_Frontend SHALL use App_Bridge redirect
7. THE Remix_Frontend SHALL handle App_Bridge authentication errors gracefully

### Requirement 14: OAuth and Session Management

**User Story:** As a shop owner, I want to authenticate securely with my Shopify store, so that the app can access my data safely.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL implement OAuth flow using Shopify App Bridge authentication
2. WHEN a shop installs the app, THE Remix_Frontend SHALL request required scopes
3. WHEN OAuth completes, THE Remix_Frontend SHALL store session token securely
4. THE Remix_Frontend SHALL include Session_Token in all API requests to Django_Backend
5. WHEN Session_Token expires, THE Remix_Frontend SHALL refresh authentication
6. THE Django_Backend SHALL validate Session_Token for all API requests
7. WHEN Session_Token is invalid, THE Django_Backend SHALL return HTTP 401

### Requirement 15: Webhook Handling

**User Story:** As a system, I want to handle Shopify webhooks, so that I can respond to shop events appropriately.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL provide a webhook endpoint at `/webhooks/app/uninstalled`
2. WHEN app uninstalled webhook is received, THE Remix_Frontend SHALL clean up shop data
3. THE Remix_Frontend SHALL provide a webhook endpoint at `/webhooks/app/scopes_update`
4. WHEN scopes update webhook is received, THE Remix_Frontend SHALL update stored scopes
5. THE Remix_Frontend SHALL verify webhook HMAC signatures
6. WHEN webhook signature is invalid, THE Remix_Frontend SHALL return HTTP 401

### Requirement 16: Error Handling and Loading States

**User Story:** As a user, I want clear feedback when operations fail or are in progress, so that I understand the system state.

#### Acceptance Criteria

1. WHEN any API request is in progress, THE Remix_Frontend SHALL display appropriate loading state using Polaris components
2. WHEN an API request fails, THE Remix_Frontend SHALL display error message using Polaris Banner component
3. WHEN a network error occurs, THE Remix_Frontend SHALL display user-friendly error message
4. WHEN a validation error occurs, THE Remix_Frontend SHALL display field-level errors using Polaris InlineError component
5. THE Remix_Frontend SHALL log errors to console for debugging
6. THE Remix_Frontend SHALL provide retry functionality for failed operations
7. WHEN an unexpected error occurs, THE Remix_Frontend SHALL display generic error message without exposing technical details

### Requirement 17: Responsive Design and Accessibility

**User Story:** As a user, I want the app to work well on different screen sizes and be accessible, so that I can use it effectively.

#### Acceptance Criteria

1. THE Remix_Frontend SHALL use Polaris responsive layout components
2. THE Remix_Frontend SHALL render correctly on desktop, tablet, and mobile viewports
3. THE Remix_Frontend SHALL follow Polaris accessibility guidelines
4. THE Remix_Frontend SHALL provide keyboard navigation for all interactive elements
5. THE Remix_Frontend SHALL use semantic HTML elements
6. THE Remix_Frontend SHALL provide appropriate ARIA labels for screen readers
7. THE Remix_Frontend SHALL maintain color contrast ratios per WCAG 2.1 AA standards

### Requirement 18: Code Organization and Architecture

**User Story:** As a developer, I want clear separation of concerns and modular code, so that the system is maintainable and extensible.

#### Acceptance Criteria

1. THE Django_Backend SHALL organize API endpoints in a dedicated `api` Django app
2. THE Django_Backend SHALL use Django REST Framework ViewSets for API views
3. THE Django_Backend SHALL use Django REST Framework Serializers for data transformation
4. THE Django_Backend SHALL NOT duplicate existing business logic
5. THE Remix_Frontend SHALL organize components in a `components` directory
6. THE Remix_Frontend SHALL organize API client code in a `services` directory
7. THE Remix_Frontend SHALL use TypeScript for type safety
8. THE Remix_Frontend SHALL follow Remix conventions for routes and loaders
9. THE Remix_Frontend SHALL NOT include custom CSS outside Polaris tokens
10. THE Remix_Frontend SHALL NOT use alternative UI frameworks

### Requirement 19: Coexistence with Existing UI

**User Story:** As a system administrator, I want both UIs to coexist, so that I can migrate gradually without disruption.

#### Acceptance Criteria

1. THE Django_Backend SHALL continue serving existing Django templates unchanged
2. THE Django_Backend SHALL maintain existing URL routes unchanged
3. THE API_Layer SHALL use a distinct URL namespace `/api/admin/`
4. THE Remix_Frontend SHALL be accessible at a distinct URL path
5. THE Django_Backend SHALL NOT modify existing models or business logic
6. WHEN the embedded app is accessed, THE existing Django UI SHALL remain functional
7. WHEN the existing Django UI is accessed, THE embedded app SHALL remain functional

### Requirement 20: Performance and Optimization

**User Story:** As a user, I want the app to load quickly and respond promptly, so that I can work efficiently.

#### Acceptance Criteria

1. WHEN the dashboard loads, THE Remix_Frontend SHALL display initial content within 2 seconds
2. WHEN a list view loads, THE Remix_Frontend SHALL display initial content within 2 seconds
3. THE API_Layer SHALL implement pagination for list endpoints with default page size of 50
4. THE API_Layer SHALL use database query optimization to minimize N+1 queries
5. THE Remix_Frontend SHALL implement client-side caching for frequently accessed data
6. THE Remix_Frontend SHALL use Remix loader functions for server-side data fetching
7. THE Remix_Frontend SHALL prefetch data for likely navigation targets
