# Implementation and Migration Plan

## Phase 1: Foundation (Current)
Goal: Establish the module structure, base client, and error handling without affecting existing code.

1.  **Scaffold Module**: Create `shopify_client` directory and subdirectories.
2.  **Define Architecture**: Create `DESIGN.md` (Done).
3.  **Implement Core Components**:
    -   `exceptions.py`: Define custom exception hierarchy.
    -   `client.py`: Implement `ShopifyGraphQLClient` using `gql` and `RequestsHTTPTransport`.
    -   `queries/`: Add initial query definitions (e.g., `products.py`).
4.  **Verification**: Verify the client works in isolation using mocks.

## Phase 2: Migration Strategy
Goal: Incrementally replace existing ad-hoc GraphQL calls with the new client.

### Step 1: Inventory & Products
-   Analyze usage in `shopify_models/graphql.py` and `shopify_models/services/inventory.py`.
-   Add necessary queries to `shopify_client/queries/inventory.py` and `products.py`.
-   Add semantic methods to `ShopifyGraphQLClient` (e.g., `update_inventory_quantity`).
-   Refactor `shopify_models` to use `ShopifyGraphQLClient`.

### Step 2: Pricing
-   Analyze usage in `prices/services.py`.
-   Add queries for Catalogs and PriceLists to `shopify_client/queries/pricing.py`.
-   Add methods: `get_catalog_by_title`, `create_price_list`, `sync_variant_prices`.
-   Refactor `prices/services.py` to inject or instantiate `ShopifyGraphQLClient`.

### Step 3: Fulfillment & Registration
-   Analyze usage in `accounts/shopify_fulfillment_app_registration.py`.
-   Add mutation for `fulfillmentServiceCreate`.
-   Refactor the registration logic to use the client.

## Future Improvements
-   Add retry logic (backoff) for throttling (handling `extensions.cost`).
-   Add logging middleware.
-   Consider async support if the rest of the application moves in that direction.
