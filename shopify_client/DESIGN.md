# Shopify GraphQL Client - Architecture Design

## Overview
The `shopify_client` module acts as a centralized infrastructure client for interacting with the Shopify Admin GraphQL API. It provides a clean, synchronous Python interface for the rest of the system, abstracting away the underlying GraphQL implementation details, transport logic, and error handling.

## Core Responsibilities
1.  **Transport Management**: Handles HTTP connections, authentication (Access Token), and headers.
2.  **GraphQL Execution**: Executes queries and mutations using the `gql` library.
3.  **Response Processing**: Normalizes GraphQL responses into plain Python objects (dicts or simple DTOs), ensuring no `gql` artifacts (like `ExecutionResult`) leak to the caller.
4.  **Error Handling**: Centralizes error detection (network, GraphQL errors, user errors) and raises specific custom exceptions.

## Architectural Boundaries
-   **Infrastructure Layer**: This module is strictly infrastructure. It contains NO business logic or flow control.
-   **Internal Implementation**: Uses `gql` with `RequestsHTTPTransport` (synchronous).
-   **External Interface**: Exposes a `ShopifyGraphQLClient` class with semantic methods (e.g., `get_product_by_sku`). It does NOT expose generic `execute` methods that accept raw query strings from outside.
-   **Isolation**: The rest of the system should not need to import `gql` or parse raw GraphQL error lists.

## Public API
The client exposes explicit, semantic methods.

```python
class ShopifyGraphQLClient:
    def __init__(self, shop_domain: str, access_token: str, api_version: str):
        ...

    def get_product_by_sku(self, sku: str) -> Optional[dict]:
        """Fetches a product by its SKU."""
        ...

    def update_inventory(self, inventory_item_id: str, quantity: int) -> dict:
        """Updates inventory for a specific item."""
        ...
```

## Query Management
Queries are defined as constant Python strings located in `shopify_client/queries/`.
-   Queries are internal to the client.
-   They are organized by domain (e.g., `products.py`, `inventory.py`).

## Error Model
The client converts low-level errors into domain-agnostic exceptions:

-   `ShopifyClientError`: Base class for all client exceptions.
-   `ShopifyAuthError`: Authentication failures (401/403).
-   `ShopifyGraphQLError`: GraphQL-level errors (syntax, validation, internal server errors).
-   `ShopifyNetworkError`: underlying connection issues.

## Testing Strategy
-   The client is designed to be easily mocked at the class boundary using `unittest.mock`.
-   Tests should mock `ShopifyGraphQLClient.get_product_by_sku` rather than mocking the underlying HTTP requests or `gql.Client` when testing business logic.
