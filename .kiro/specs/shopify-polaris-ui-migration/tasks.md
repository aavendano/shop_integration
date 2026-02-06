# Implementation Plan: Shopify Polaris UI Migration

## Current Implementation Status

**Completed:**
- ✅ Task 1: Django REST Framework API infrastructure is fully set up
- ✅ Task 1.1 & 1.2: Property-based tests for API namespace and authentication are implemented
- ✅ Task 2: Context API endpoint is fully implemented and tested

**In Progress:**
- None

**Next Steps:**
- Task 3: Implement Products API endpoints (serializers, views, and tests)
- Task 7: Set up Remix frontend infrastructure (requires Shopify CLI initialization)

**Important Notes:**
- The backend API layer is ready for Products, Inventory, Jobs, and Orders endpoints
- No Remix frontend exists yet - this needs to be initialized as a separate Shopify app
- All existing Django models and business logic remain unchanged
- The middleware properly validates JWT session tokens from Shopify App Bridge

## Overview

This implementation plan breaks down the Shopify Polaris UI migration into discrete, incremental tasks. Each task builds on previous work, ensuring continuous integration and early validation. The plan follows a backend-first approach, establishing the API layer before building the frontend views.

The implementation maintains strict separation between the new embedded UI and existing Django templates, ensuring both systems coexist without interference.

## Tasks

- [x] 1. Set up Django REST Framework API infrastructure
  - Create new `api` Django app with proper structure
  - Configure URL routing under `/api/admin/` namespace
  - Set up Django REST Framework in settings
  - Create base authentication middleware for session token validation
  - _Requirements: 1.1, 1.2, 1.3, 18.1, 18.2, 19.3_

- [x] 1.1 Write property test for API namespace consistency
  - **Property 1: API Namespace Consistency**
  - **Validates: Requirements 1.1**

- [x] 1.2 Write property test for authentication enforcement
  - **Property 2: Authentication Enforcement**
  - **Validates: Requirements 1.2, 1.3, 14.6**

- [x] 2. Implement Context API endpoint
  - [x] 2.1 Create context serializer for shop and user data
    - Serialize Shop model with myshopify_domain, name, domain, currency
    - Serialize User model with id, username, email
    - Include permissions flags based on shop configuration
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [x] 2.2 Create context view with session validation
    - Implement GET endpoint at `/api/admin/context/`
    - Return shop, user, and permissions data
    - Handle missing session with HTTP 404
    - _Requirements: 2.1, 2.5_
  
  - [x] 2.3 Write unit tests for context endpoint
    - Test successful context retrieval
    - Test missing session returns 404
    - Test response structure
    - _Requirements: 2.1, 2.2, 2.5_

- [ ] 3. Implement Products API endpoints
  - [x] 3.1 Create product serializers
    - Implement ProductListSerializer with variant_count and sync_status
    - Implement ProductDetailSerializer with images and variants
    - Implement VariantSerializer with inventory data
    - Implement ImageSerializer
    - _Requirements: 3.5, 3.7, 1.4_
  
  - [x] 3.2 Create products list view with filtering and pagination
    - Implement GET endpoint at `/api/admin/products/`
    - Add pagination with configurable page size (default 50)
    - Add filters for title, vendor, product_type, tags
    - Add sorting for created_at, updated_at, title
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 20.3_
  
  - [x] 3.3 Create product detail view
    - Implement GET endpoint at `/api/admin/products/{id}/`
    - Return complete product with variants, images, inventory
    - Use select_related and prefetch_related for query optimization
    - _Requirements: 3.6, 3.7, 20.4_
  
  - [x] 3.4 Create product sync endpoint
    - Implement POST endpoint at `/api/admin/products/{id}/sync/`
    - Call existing Product.export_to_shopify() method
    - Return sync results with success/error status
    - _Requirements: 3.8, 3.9, 3.10, 3.11_
  
  - [x] 3.5 Create bulk sync endpoint
    - Implement POST endpoint at `/api/admin/products/bulk-sync/`
    - Accept array of product IDs
    - Process each product and aggregate results
    - _Requirements: 3.12, 3.13, 3.14_



- [ ]* 3.6 Write property tests for products API
  - **Property 3: Render-Ready Response Structure**
  - **Property 5: Pagination Consistency**
  - **Property 6: Filter Correctness**
  - **Property 7: Sort Order Correctness**
  - **Property 8: Bulk Operation Completeness**
  - **Property 11: Business Logic Delegation**
  - **Property 12: Query Optimization**
  - **Validates: Requirements 1.4, 3.2, 3.3, 3.4, 3.9, 3.13, 3.14, 20.4**

- [ ]* 3.7 Write unit tests for products API
  - Test product list with known data
  - Test product detail response structure
  - Test sync success and failure cases
  - Test bulk sync with mixed results
  - _Requirements: 3.1, 3.6, 3.10, 3.11_

- [ ] 4. Implement Inventory API endpoints
  - [x] 4.1 Create inventory serializer
    - Serialize inventory items with product and variant info
    - Include source_quantity, tracked, sync_pending status
    - _Requirements: 4.2, 4.3_
  
  - [x] 4.2 Create inventory list view with filtering
    - Implement GET endpoint at `/api/admin/inventory/`
    - Filter for tracked variants only
    - Add filters for product_title and SKU
    - Add pagination
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 4.3 Create inventory reconcile endpoint
    - Implement POST endpoint at `/api/admin/inventory/reconcile/`
    - Synchronize inventory quantities with Shopify
    - Return reconciliation results
    - _Requirements: 4.5, 4.6, 4.7_

- [ ]* 4.4 Write property tests for inventory API
  - **Property 9: Inventory Tracking Filter**
  - **Property 10: Inventory Filter Correctness**
  - **Validates: Requirements 4.2, 4.4**

- [ ]* 4.5 Write unit tests for inventory API
  - Test inventory list with tracked variants
  - Test inventory filters
  - Test reconciliation
  - _Requirements: 4.1, 4.5, 4.7_

- [ ] 5. Implement Jobs API endpoints
  - [x] 5.1 Create job serializer
    - Serialize job data with type, status, progress, timestamps
    - Include logs and error messages
    - _Requirements: 6.2_
  
  - [x] 5.2 Create jobs list view with filtering
    - Implement GET endpoint at `/api/admin/jobs/`
    - Add filters for status and job_type
    - Add pagination
    - _Requirements: 6.1, 6.3_
  
  - [x] 5.3 Create job detail view
    - Implement GET endpoint at `/api/admin/jobs/{id}/`
    - Return complete job information with logs
    - _Requirements: 6.4, 6.5_

- [ ]* 5.4 Write unit tests for jobs API
  - Test jobs list with various statuses
  - Test job detail response
  - Test filtering by status and type
  - _Requirements: 6.1, 6.4_

- [x] 6. Checkpoint - Backend API layer complete
  - Ensure all API endpoints are functional
  - Verify authentication works correctly
  - Run all backend tests
  - Ask the user if questions arise



- [x] 7. Set up Remix frontend infrastructure
  - Initialize new Remix app using Shopify CLI (`npm init @shopify/app@latest`)
  - Configure TypeScript and project structure
  - Set up Shopify App Bridge and Polaris dependencies
  - Create TypeScript types for API responses in `app/types/`
  - Create base API client service in `app/services/api.ts`
  - Configure environment variables for Django API URL
  - Set up error handling utilities
  - _Requirements: 18.7, 18.8_

- [x] 8. Implement API client services
  - [x] 8.1 Create products service
    - Implement ProductsService class with list, get, sync, bulkSync methods
    - Define TypeScript interfaces for Product, ProductDetail, ProductsListResponse
    - _Requirements: 3.1, 3.6, 3.8, 3.12_
  
  - [x] 8.2 Create inventory service
    - Implement InventoryService class with list and reconcile methods
    - Define TypeScript interfaces for inventory data
    - _Requirements: 4.1, 4.5_
  
  - [x] 8.3 Create jobs service
    - Implement JobsService class with list and get methods
    - Define TypeScript interfaces for job data
    - _Requirements: 6.1, 6.4_
  
  - [x] 8.4 Create context service
    - Implement ContextService class with getContext method
    - Define TypeScript interfaces for context data
    - _Requirements: 2.1_

- [ ]* 8.5 Write property test for session token inclusion
  - **Property 21: Session Token Inclusion**
  - **Validates: Requirements 14.4**

- [x] 9. Implement Dashboard view
  - [x] 9.1 Create dashboard route at `/app`
    - Implement loader to fetch context and metrics
    - Display key metrics using Polaris Card components
    - Show product count, pending sync count, inventory count, recent jobs
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [x] 9.2 Add loading and error states
    - Display SkeletonPage while loading
    - Display Banner on error
    - _Requirements: 7.7, 7.8_

- [ ]* 9.3 Write unit tests for dashboard
  - Test metrics display
  - Test loading state
  - Test error state
  - _Requirements: 7.2, 7.7, 7.8_

- [x] 10. Implement Products List view
  - [x] 10.1 Create products list route at `/app/products`
    - Implement loader to fetch products with pagination
    - Display products using Polaris IndexTable component
    - Show columns: image, title, vendor, type, variant count, sync status
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 10.2 Add filters and sorting
    - Implement Polaris Filters component for title, vendor, product_type, tags
    - Add sorting options for created date, updated date, title
    - _Requirements: 8.6, 8.7_
  
  - [x] 10.3 Add pagination
    - Implement Polaris Pagination component
    - Handle page navigation
    - _Requirements: 8.8_
  
  - [x] 10.4 Add bulk actions
    - Implement bulk sync action
    - Show confirmation modal using Polaris Modal
    - Display Toast notification on completion
    - _Requirements: 8.9, 8.10, 8.11_
  
  - [x] 10.5 Add loading and empty states
    - Display SkeletonPage while loading
    - Display EmptyState when no products exist
    - _Requirements: 8.4, 8.5_

- [ ]* 10.6 Write property tests for products list
  - **Property 13: Polaris Component Usage**
  - **Property 14: Loading State Display**
  - **Property 16: Bulk Action Availability**
  - **Property 17: Toast Notification on Completion**
  - **Validates: Requirements 7.2, 8.2, 8.4, 8.9, 8.11**



- [x] 11. Implement Product Detail view
  - [x] 11.1 Create product detail route at `/app/products/$id`
    - Implement loader to fetch product details
    - Display product info using Polaris Layout and Card components
    - Show product title, description, vendor, type, tags
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 11.2 Display product images
    - Show images using Polaris Thumbnail component
    - Handle multiple images with proper positioning
    - _Requirements: 9.4_
  
  - [x] 11.3 Display variants table
    - Show variants using Polaris DataTable component
    - Display columns: title, SKU, price, inventory, sync status
    - _Requirements: 9.5, 9.6_
  
  - [x] 11.4 Add sync functionality
    - Implement sync button using Polaris Button component
    - Show loading state during sync
    - Display Toast notification on completion
    - _Requirements: 9.7, 9.8, 9.9, 9.10_
  
  - [x] 11.5 Add loading and error states
    - Display SkeletonPage while loading
    - Display EmptyState when product not found
    - _Requirements: 9.11, 9.12_

- [ ]* 11.6 Write property tests for product detail
  - **Property 18: API Call Integration**
  - **Validates: Requirements 9.8**

- [ ]* 11.7 Write unit tests for product detail
  - Test product detail display
  - Test sync button functionality
  - Test loading and error states
  - _Requirements: 9.2, 9.10, 9.11_

- [x] 12. Implement Inventory view
  - [x] 12.1 Create inventory route at `/app/inventory`
    - Implement loader to fetch inventory items
    - Display inventory using Polaris IndexTable component
    - Show columns: product, variant, SKU, quantity, sync status
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 12.2 Add filters
    - Implement Polaris Filters component for product title and SKU
    - _Requirements: 10.4_
  
  - [x] 12.3 Add reconcile functionality
    - Implement reconcile button using Polaris Button component
    - Display Toast notification on completion
    - _Requirements: 10.5, 10.6, 10.7_
  
  - [x] 12.4 Add loading state
    - Display SkeletonPage while loading
    - _Requirements: 10.8_

- [ ]* 12.5 Write unit tests for inventory view
  - Test inventory list display
  - Test filters
  - Test reconcile functionality
  - _Requirements: 10.2, 10.4, 10.7_

- [x] 13. Implement Jobs view
  - [x] 13.1 Create jobs list route at `/app/jobs`
    - Implement loader to fetch jobs
    - Display jobs using Polaris IndexTable component
    - Show columns: job type, status, progress, started time, duration
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [x] 13.2 Add status badges and progress bars
    - Use Polaris Badge component for job status
    - Use Polaris ProgressBar component for progress
    - _Requirements: 11.4, 11.5_
  
  - [x] 13.3 Add filters
    - Implement filters for job status and type
    - _Requirements: 11.6_
  
  - [x] 13.4 Add job detail navigation
    - Navigate to job detail on row click
    - _Requirements: 11.7_
  
  - [x] 13.5 Add auto-refresh for active jobs
    - Refresh job list every 5 seconds when active jobs exist
    - _Requirements: 11.8_
  
  - [x] 13.6 Add loading state
    - Display SkeletonPage while loading
    - _Requirements: 11.9_

- [ ]* 13.7 Write unit tests for jobs view
  - Test jobs list display
  - Test status badges and progress bars
  - Test filters
  - Test auto-refresh
  - _Requirements: 11.2, 11.4, 11.5, 11.8_



- [x] 14. Implement Settings view
  - [x] 14.1 Create settings route at `/app/settings`
    - Implement loader to fetch shop info and settings
    - Display settings using Polaris Layout and Card components
    - Show shop information: name, domain, currency
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [x] 14.2 Display pricing configuration
    - Show pricing configuration status
    - _Requirements: 12.4_
  
  - [x] 14.3 Add sync preferences
    - Display sync preferences using Polaris ChoiceList component
    - _Requirements: 12.5_
  
  - [x] 14.4 Add save functionality
    - Implement save button using Polaris Button component
    - Validate and submit settings
    - Display Toast notification on save
    - _Requirements: 12.6, 12.7, 12.8_

- [ ]* 14.5 Write unit tests for settings view
  - Test settings display
  - Test save functionality
  - Test validation
  - _Requirements: 12.2, 12.7, 12.8_

- [x] 15. Implement App Bridge integration
  - [x] 15.1 Configure App Bridge initialization
    - Initialize App Bridge on application load
    - Configure with API key and shop domain
    - _Requirements: 13.1_
  
  - [x] 15.2 Implement App Bridge navigation
    - Use App Bridge for navigation within embedded app
    - Update browser URL using App Bridge
    - _Requirements: 13.2, 13.5_
  
  - [x] 15.3 Implement App Bridge Toast
    - Use App Bridge Toast for all notifications
    - Replace Polaris Toast with App Bridge Toast
    - _Requirements: 13.3_
  
  - [x] 15.4 Implement TitleBar for all pages
    - Use App Bridge TitleBar for page titles and actions
    - _Requirements: 13.4_
  
  - [x] 15.5 Handle external links
    - Use App Bridge redirect for external links
    - _Requirements: 13.6_
  
  - [x] 15.6 Handle authentication errors
    - Gracefully handle App Bridge authentication errors
    - _Requirements: 13.7_

- [ ]* 15.7 Write property tests for App Bridge integration
  - **Property 19: App Bridge Navigation**
  - **Property 20: App Bridge Toast Usage**
  - **Validates: Requirements 13.2, 13.3**

- [-] 16. Implement OAuth and session management
  - [x] 16.1 Configure OAuth flow
    - Implement OAuth flow using Shopify App Bridge authentication
    - Request required scopes on installation
    - _Requirements: 14.1, 14.2_
  
  - [x] 16.2 Implement session token storage
    - Store session token securely after OAuth completion
    - _Requirements: 14.3_
  
  - [x] 16.3 Add session token to API requests
    - Include Session_Token in Authorization header for all API requests
    - _Requirements: 14.4_
  
  - [x] 16.4 Handle token expiration
    - Refresh authentication when Session_Token expires
    - _Requirements: 14.5_
  
  - [x] 16.5 Implement backend token validation
    - Validate Session_Token in Django authentication middleware
    - Return HTTP 401 for invalid tokens
    - _Requirements: 14.6, 14.7_

- [x]* 16.6 Write property tests for authentication
  - **Property 4: Structured Error Responses**
  - **Validates: Requirements 1.7, 14.7**



- [x] 17. Implement webhook handling
  - [x] 17.1 Create app uninstalled webhook endpoint
    - Implement POST endpoint at `/webhooks/app/uninstalled`
    - Clean up shop data on app uninstall
    - _Requirements: 15.1, 15.2_
  
  - [x] 17.2 Create scopes update webhook endpoint
    - Implement POST endpoint at `/webhooks/app/scopes_update`
    - Update stored scopes on scopes change
    - _Requirements: 15.3, 15.4_
  
  - [x] 17.3 Add webhook signature verification
    - Verify webhook HMAC signatures
    - Return HTTP 401 for invalid signatures
    - _Requirements: 15.5, 15.6_

- [ ]* 17.4 Write unit tests for webhooks
  - Test app uninstalled webhook
  - Test scopes update webhook
  - Test signature verification
  - _Requirements: 15.2, 15.4, 15.6_

- [x] 18. Implement comprehensive error handling
  - [x] 18.1 Add loading states to all views
    - Display appropriate loading state for all API requests
    - Use Polaris SkeletonPage, SkeletonBodyText, or Spinner
    - _Requirements: 16.1_
  
  - [x] 18.2 Add error display to all views
    - Display error messages using Polaris Banner component
    - Show user-friendly error messages for network errors
    - _Requirements: 16.2, 16.3_
  
  - [x] 18.3 Add field-level validation errors
    - Display validation errors using Polaris InlineError component
    - _Requirements: 16.4_
  
  - [x] 18.4 Add error logging
    - Log errors to console for debugging
    - _Requirements: 16.5_
  
  - [x] 18.5 Add retry functionality
    - Provide retry functionality for failed operations
    - _Requirements: 16.6_
  
  - [x] 18.6 Add generic error handling
    - Display generic error message for unexpected errors
    - Avoid exposing technical details to users
    - _Requirements: 16.7_

- [ ]* 18.7 Write property tests for error handling
  - **Property 15: Error Display Consistency**
  - **Validates: Requirements 16.2**

- [x] 19. Implement responsive design and accessibility
  - [x] 19.1 Use Polaris responsive layout components
    - Ensure all views use Polaris responsive components
    - _Requirements: 17.1_
  
  - [x] 19.2 Test responsive behavior
    - Verify rendering on desktop, tablet, and mobile viewports
    - _Requirements: 17.2_
  
  - [x] 19.3 Implement keyboard navigation
    - Provide keyboard navigation for all interactive elements
    - _Requirements: 17.4_
  
  - [x] 19.4 Add semantic HTML and ARIA labels
    - Use semantic HTML elements
    - Provide appropriate ARIA labels for screen readers
    - _Requirements: 17.5, 17.6_
  
  - [x] 19.5 Verify color contrast
    - Maintain color contrast ratios per WCAG 2.1 AA standards
    - _Requirements: 17.7_

- [ ]* 19.6 Write accessibility tests
  - Test keyboard navigation
  - Test ARIA labels
  - Test color contrast
  - _Requirements: 17.3, 17.4, 17.6, 17.7_

- [x] 20. Verify coexistence with existing UI
  - [x] 20.1 Test existing Django UI functionality
    - Verify all existing Django URL routes work unchanged
    - Test existing Django views and templates
    - _Requirements: 19.1, 19.2_
  
  - [x] 20.2 Test API namespace separation
    - Verify API endpoints use distinct `/api/admin/` namespace
    - Ensure no conflicts with existing URLs
    - _Requirements: 19.3_
  
  - [x] 20.3 Test simultaneous access
    - Verify both UIs can be accessed simultaneously
    - Test that changes in one UI don't affect the other
    - _Requirements: 19.4, 19.6, 19.7_
  
  - [x] 20.4 Verify no backend modifications
    - Confirm existing models and business logic unchanged
    - Verify API layer delegates to existing logic
    - _Requirements: 19.5_

- [ ]* 20.5 Write property tests for coexistence
  - **Property 22: Backward Compatibility**
  - **Property 23: UI Coexistence**
  - **Validates: Requirements 19.1, 19.6**

- [x] 21. Final checkpoint - Complete system integration
  - Run all tests (unit, property, integration)
  - Verify all views are functional
  - Test complete user flows
  - Verify performance requirements
  - Ensure all tests pass, ask the user if questions arise



## Notes

- Tasks marked with `*` are optional test-related sub-tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Backend uses Python with Django REST Framework
- Frontend uses TypeScript with Remix, React, and Shopify Polaris
- All API endpoints must use `/api/admin/` namespace
- All UI components must be from Shopify Polaris library
- No modifications to existing Django models or business logic
- Both UIs (Django templates and Remix embedded app) must coexist independently

## Implementation Order Rationale

1. **Backend First**: Establish API layer before frontend to enable parallel development
2. **Core Endpoints First**: Context and Products APIs are foundational for other features
3. **Incremental UI**: Build views progressively, starting with most critical (Dashboard, Products)
4. **Integration Last**: App Bridge and OAuth integration after core functionality works
5. **Testing Throughout**: Property and unit tests as sub-tasks to catch issues early
6. **Checkpoints**: Strategic validation points to ensure quality before proceeding

## Testing Configuration

**Backend (pytest + Hypothesis):**
- Minimum 100 iterations per property test
- Tag format: `# Feature: shopify-polaris-ui-migration, Property N: [property text]`
- Use pytest-django for database access
- Use factory_boy for test data generation

**Frontend (Vitest + fast-check):**
- Minimum 100 iterations per property test
- Tag format: `// Feature: shopify-polaris-ui-migration, Property N: [property text]`
- Use MSW for API mocking
- Use @shopify/app-bridge-react test utilities

**Integration (Playwright):**
- Test complete user flows
- Test embedded app in Shopify Admin context
- Test authentication and session management
