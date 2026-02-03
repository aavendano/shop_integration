from typing import Optional, Dict, Any, List
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
from requests.exceptions import RequestException

from .exceptions import (
    ShopifyClientError,
    ShopifyGraphQLError,
    ShopifyAuthError,
    ShopifyNetworkError,
)
from .queries.products import GET_PRODUCT_BY_SKU
from .queries.inventory import (
    INVENTORY_ITEMS_PAGE,
    LOCATION_INVENTORY_LEVELS_PAGE,
    VARIANT_INVENTORY_ITEM_ID,
    INVENTORY_ITEM_UPDATE,
    INVENTORY_SET_QUANTITIES,
    LOCATION_BY_ID,
    INVENTORY_LEVELS_BY_ITEM,
)


class ShopifyGraphQLClient:
    def __init__(self, shop_domain: str, access_token: str, api_version: str):
        """
        Initialize the Shopify GraphQL Client.

        Args:
            shop_domain: The domain of the Shopify store (e.g., 'mystore.myshopify.com').
            access_token: The Admin API access token.
            api_version: The API version (e.g., '2023-10').
        """
        self.shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")
        self.api_version = api_version
        self.access_token = access_token
        self._client = self._setup_client()

    @property
    def endpoint(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"

    def _setup_client(self) -> Client:
        transport = RequestsHTTPTransport(
            url=self.endpoint,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token,
            },
            verify=True,
            retries=3,
        )
        return Client(transport=transport, fetch_schema_from_transport=False)

    def _execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to execute GraphQL queries.

        Args:
            query: The GraphQL query string.
            variables: Optional dictionary of variables.

        Returns:
            The 'data' dictionary from the response.

        Raises:
            ShopifyGraphQLError: If the response contains GraphQL errors.
            ShopifyAuthError: If authentication fails (401/403).
            ShopifyNetworkError: If a network error occurs.
            ShopifyClientError: For other unexpected errors.
        """
        try:
            document = gql(query)
            return self._client.execute(document, variable_values=variables)
        except TransportQueryError as e:
            # GraphQL application-level errors
            errors = e.errors or []
            msg = errors[0].get("message") if errors else str(e)
            raise ShopifyGraphQLError(f"Shopify GraphQL Error: {msg}", errors=errors) from e
        except TransportServerError as e:
            # HTTP level errors (4xx, 5xx)
            if e.code in (401, 403):
                raise ShopifyAuthError(f"Authentication failed: {e.code}") from e
            raise ShopifyNetworkError(f"Network error: {e.code}") from e
        except RequestException as e:
            # Underlying requests library errors
            raise ShopifyNetworkError(f"Connection failed: {str(e)}") from e
        except Exception as e:
            raise ShopifyClientError(f"Unexpected error: {str(e)}") from e

    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single product by its SKU.

        Args:
            sku: The Stock Keeping Unit.

        Returns:
            A dictionary containing product data if found, else None.
        """
        # Shopify 'query' filter syntax: "sku:value"
        query_str = f"sku:{sku}"
        variables = {"query": query_str}

        response = self._execute(GET_PRODUCT_BY_SKU, variables)

        # Normalize response structure
        # Expected path: products -> edges -> node
        products_data = response.get("products", {})
        edges = products_data.get("edges", [])

        if not edges:
            return None

        # Return the first matching node
        return edges[0].get("node")

    def get_inventory_items_page(
        self,
        *,
        first: int,
        after: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        variables = {"first": first, "after": after, "query": query}
        return self._execute(INVENTORY_ITEMS_PAGE, variables)

    def get_location_inventory_levels_page(
        self,
        *,
        location_id: str,
        first: int,
        after: Optional[str] = None,
        updated_at_query: Optional[str] = None,
        quantity_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        variables = {
            "locationId": location_id,
            "first": first,
            "after": after,
            "updatedAtQuery": updated_at_query,
            "quantityNames": quantity_names or ["available", "incoming", "on_hand"],
        }
        return self._execute(LOCATION_INVENTORY_LEVELS_PAGE, variables)

    def get_variant_inventory_item_id(self, variant_id: str) -> Optional[str]:
        data = self._execute(VARIANT_INVENTORY_ITEM_ID, {"id": variant_id})
        return (
            data.get("productVariant", {})
            .get("inventoryItem", {})
            .get("id")
        )

    def update_inventory_item_cost(
        self,
        *,
        inventory_item_id: str,
        cost: str,
    ) -> List[Dict[str, Any]]:
        variables = {
            "id": inventory_item_id,
            "input": {"cost": cost},
        }
        data = self._execute(INVENTORY_ITEM_UPDATE, variables)
        return data.get("inventoryItemUpdate", {}).get("userErrors", [])

    def set_inventory_quantities(
        self,
        *,
        name: str,
        reason: str,
        quantities: List[Dict[str, Any]],
        ignore_compare_quantity: bool = True,
    ) -> List[Dict[str, Any]]:
        variables = {
            "input": {
                "name": name,
                "reason": reason,
                "quantities": quantities,
                "ignoreCompareQuantity": ignore_compare_quantity,
            }
        }
        data = self._execute(INVENTORY_SET_QUANTITIES, variables)
        return data.get("inventorySetQuantities", {}).get("userErrors", [])

    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        data = self._execute(LOCATION_BY_ID, {"id": location_id})
        return data.get("location") if data else None

    def get_inventory_levels(
        self,
        *,
        inventory_item_id: str,
        first: int = 10,
        quantity_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        variables = {
            "inventoryItemId": inventory_item_id,
            "first": first,
            "quantityNames": quantity_names or ["available"],
        }
        data = self._execute(INVENTORY_LEVELS_BY_ITEM, variables)
        return (
            data.get("inventoryItem", {})
            .get("inventoryLevels", {})
            .get("edges", [])
            if data
            else []
        )
