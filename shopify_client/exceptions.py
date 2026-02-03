from typing import List, Optional, Any

class ShopifyClientError(Exception):
    """Base exception for all Shopify Client errors."""
    pass

class ShopifyAuthError(ShopifyClientError):
    """Raised when authentication fails (401/403)."""
    pass

class ShopifyNetworkError(ShopifyClientError):
    """Raised when the network connection fails."""
    pass

class ShopifyGraphQLError(ShopifyClientError):
    """Raised when the GraphQL response contains errors."""
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message)
        self.errors = errors or []
