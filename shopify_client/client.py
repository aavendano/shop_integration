import time
from typing import Optional, Dict, Any, Iterable, List, Tuple, Union
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
    INVENTORY_ITEMS_PAGE_QUERY,
    LOCATION_INVENTORY_LEVELS_QUERY,
    LOCATIONS_PAGE_QUERY,
    INVENTORY_ITEMS_PAGE,
    LOCATION_INVENTORY_LEVELS_PAGE,
    VARIANT_INVENTORY_ITEM_ID,
    INVENTORY_ITEM_UPDATE,
    INVENTORY_SET_QUANTITIES,
    LOCATION_BY_ID,
    INVENTORY_LEVELS_BY_ITEM,
)
from .queries.pricing import (
    GET_CATALOG_BY_TITLE,
    GET_PRICE_LISTS,
    CREATE_CATALOG,
    CREATE_PRICE_LIST,
    PRICE_LIST_FIXED_PRICES_ADD,
)
from .queries.fulfillment import FULFILLMENT_SERVICE_CREATE


class ShopifyGraphQLClient:
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str,
        *,
        throttle: bool = True,
        min_available: int = 50,
    ):
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
        self.throttle = throttle
        self.min_available = min_available

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

    def _execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        *,
        include_extensions: bool = False,
    ) -> Union[Dict[str, Any], Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Internal method to execute GraphQL queries.

        Args:
            query: The GraphQL query string.
            variables: Optional dictionary of variables.

        Returns:
            The 'data' dictionary from the response, plus extensions when requested.

        Raises:
            ShopifyGraphQLError: If the response contains GraphQL errors.
            ShopifyAuthError: If authentication fails (401/403).
            ShopifyNetworkError: If a network error occurs.
            ShopifyClientError: For other unexpected errors.
        """
        try:
            document = gql(query)
            if include_extensions:
                result = self._client.execute(
                    document,
                    variable_values=variables,
                    get_execution_result=True,
                )
                data = result.data or {}
                extensions = result.extensions or {}
                if self.throttle:
                    self._apply_throttle(extensions)
                return data, extensions
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

    def _apply_throttle(self, extensions: Dict[str, Any]) -> None:
        cost = extensions.get("cost") or {}
        throttle_status = cost.get("throttleStatus") or {}
        available = throttle_status.get("currentlyAvailable")
        restore_rate = throttle_status.get("restoreRate")
        if (
            available is None
            or restore_rate in (None, 0)
            or available >= self.min_available
        ):
            return
        wait_seconds = (self.min_available - available) / restore_rate
        if wait_seconds <= 0:
            return
        time.sleep(wait_seconds)

    def _raise_user_errors(self, payload: Dict[str, Any], *, operation: str) -> None:
        user_errors = payload.get("userErrors") or []
        if not user_errors:
            return
        messages = "; ".join(
            error.get("message", "Unknown error") for error in user_errors
        )
        raise ShopifyGraphQLError(
            f"Shopify {operation} user errors: {messages}",
            errors=user_errors,
        )

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

        response, _extensions = self._execute(
            GET_PRODUCT_BY_SKU,
            variables,
            include_extensions=True,
        )

        # Normalize response structure
        # Expected path: products -> edges -> node
        products_data = response.get("products", {})
        edges = products_data.get("edges", [])

        if not edges:
            return None

        # Return the first matching node
        return edges[0].get("node")

    def get_catalog_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        query_str = f"title:{title}"
        variables = {"query": query_str}
        response, _extensions = self._execute(
            GET_CATALOG_BY_TITLE,
            variables,
            include_extensions=True,
        )
        catalogs_data = response.get("catalogs", {})
        edges = catalogs_data.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            if node.get("title") == title:
                return node
        return None

    def get_price_list_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        response, _extensions = self._execute(
            GET_PRICE_LISTS,
            include_extensions=True,
        )
        price_lists = response.get("priceLists", {})
        edges = price_lists.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            if node.get("name") == name:
                return node
        return None

    def create_catalog(self, title: str, country_code: str) -> Optional[Dict[str, Any]]:
        variables = {
            "input": {
                "title": title,
                "status": "ACTIVE",
                "context": {"marketIds": []},
            }
        }
        response, _extensions = self._execute(
            CREATE_CATALOG,
            variables,
            include_extensions=True,
        )
        payload = response.get("catalogCreate") or {}
        self._raise_user_errors(payload, operation="catalogCreate")
        return payload.get("catalog")

    def create_price_list(
        self,
        name: str,
        currency: str,
        catalog_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        variables = {
            "input": {
                "name": name,
                "currency": currency,
                "parent": {
                    "adjustment": {
                        "type": "PERCENTAGE_DECREASE",
                        "value": 0.0,
                    }
                },
            }
        }
        if catalog_id:
            variables["input"]["catalogId"] = catalog_id
        response, _extensions = self._execute(
            CREATE_PRICE_LIST,
            variables,
            include_extensions=True,
        )
        payload = response.get("priceListCreate") or {}
        self._raise_user_errors(payload, operation="priceListCreate")
        return payload.get("priceList")

    def sync_variant_prices(
        self,
        price_list_id: str,
        prices: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        variables = {"priceListId": price_list_id, "prices": prices}
        response, _extensions = self._execute(
            PRICE_LIST_FIXED_PRICES_ADD,
            variables,
            include_extensions=True,
        )
        payload = response.get("priceListFixedPricesAdd") or {}
        self._raise_user_errors(payload, operation="priceListFixedPricesAdd")
        return payload

    def register_fulfillment_service(
        self,
        callback_url: str,
        name: str,
        tracking_support: bool,
        inventory_management: bool,
    ) -> Optional[Dict[str, Any]]:
        variables = {
            "callbackUrl": callback_url,
            "name": name,
            "trackingSupport": tracking_support,
            "inventoryManagement": inventory_management,
        }
        response, _extensions = self._execute(
            FULFILLMENT_SERVICE_CREATE,
            variables,
            include_extensions=True,
        )
        payload = response.get("fulfillmentServiceCreate") or {}
        self._raise_user_errors(payload, operation="fulfillmentServiceCreate")
        return payload.get("fulfillmentService")

    def get_variant_inventory_item_id(self, variant_id: str) -> Optional[str]:
        variables = {"id": variant_id}
        response, _extensions = self._execute(
            VARIANT_INVENTORY_ITEM_ID,
            variables,
            include_extensions=True,
        )
        product_variant = response.get("productVariant") or {}
        inventory_item = product_variant.get("inventoryItem") or {}
        return inventory_item.get("id")

    def update_inventory_item_cost(
        self,
        *,
        inventory_item_id: str,
        cost: str,
        currency: Optional[str] = None,
    ) -> List[str]:
        input_payload: Dict[str, Any] = {"cost": {"amount": cost}}
        if currency:
            input_payload["cost"]["currencyCode"] = currency
        variables = {"id": inventory_item_id, "input": input_payload}
        response, _extensions = self._execute(
            INVENTORY_ITEM_UPDATE,
            variables,
            include_extensions=True,
        )
        payload = response.get("inventoryItemUpdate") or {}
        return [
            error.get("message", "Unknown error")
            for error in payload.get("userErrors") or []
        ]

    def set_inventory_quantities(
        self,
        *,
        name: str,
        reason: str,
        quantities: List[Dict[str, Any]],
        ignore_compare_quantity: bool = False,
    ) -> List[str]:
        variables = {
            "input": {
                "name": name,
                "reason": reason,
                "quantities": quantities,
                "ignoreCompareQuantity": ignore_compare_quantity,
            }
        }
        response, _extensions = self._execute(
            INVENTORY_SET_QUANTITIES,
            variables,
            include_extensions=True,
        )
        payload = response.get("inventorySetQuantities") or {}
        return [
            error.get("message", "Unknown error")
            for error in payload.get("userErrors") or []
        ]

    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        variables = {"id": location_id}
        response, _extensions = self._execute(
            LOCATION_BY_ID,
            variables,
            include_extensions=True,
        )
        return response.get("location")

    def get_inventory_levels(
        self,
        *,
        inventory_item_id: str,
        quantity_names: List[str],
        first: int = 20,
    ) -> List[Dict[str, Any]]:
        variables = {
            "inventoryItemId": inventory_item_id,
            "first": first,
            "quantityNames": quantity_names,
        }
        response, _extensions = self._execute(
            INVENTORY_LEVELS_BY_ITEM,
            variables,
            include_extensions=True,
        )
        inventory_item = response.get("inventoryItem") or {}
        levels = inventory_item.get("inventoryLevels") or {}
        return levels.get("edges", [])

    def get_inventory_items_page(
        self,
        *,
        first: int,
        after: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        variables = {"first": first, "after": after, "query": query}
        response, _extensions = self._execute(
            INVENTORY_ITEMS_PAGE_QUERY,
            variables,
            include_extensions=True,
        )
        return response

    def get_location_inventory_levels_page(
        self,
        *,
        location_id: str,
        first: int,
        after: Optional[str] = None,
        updated_at_query: Optional[str] = None,
        quantity_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        quantity_names = quantity_names or ["available", "incoming", "on_hand"]
        variables = {
            "locationId": location_id,
            "first": first,
            "after": after,
            "updatedAtQuery": updated_at_query,
            "quantityNames": quantity_names,
        }
        response, _extensions = self._execute(
            LOCATION_INVENTORY_LEVELS_QUERY,
            variables,
            include_extensions=True,
        )
        return response

    def list_inventory_items(
        self,
        *,
        query: Optional[str] = None,
        page_size: int = 50,
        max_pages: Optional[int] = None,
    ) -> Iterable[Dict[str, Any]]:
        variables = {"first": page_size, "after": None, "query": query}
        page = 0
        while True:
            data, _extensions = self._execute(
                INVENTORY_ITEMS_PAGE_QUERY,
                variables,
                include_extensions=True,
            )
            connection = data.get("inventoryItems", {})
            for edge in connection.get("edges", []):
                yield edge.get("node")
            page_info = connection.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            page += 1
            if max_pages is not None and page >= max_pages:
                break
            variables["after"] = page_info.get("endCursor")

    def list_location_inventory_levels(
        self,
        location_gid: str,
        *,
        updated_at_query: Optional[str] = None,
        page_size: int = 50,
        max_pages: Optional[int] = None,
        quantity_names: Optional[List[str]] = None,
    ) -> Iterable[Dict[str, Any]]:
        quantity_names = quantity_names or ["available", "incoming", "on_hand"]
        variables = {
            "locationId": location_gid,
            "first": page_size,
            "after": None,
            "updatedAtQuery": updated_at_query,
            "quantityNames": quantity_names,
        }
        page = 0
        while True:
            data, _extensions = self._execute(
                LOCATION_INVENTORY_LEVELS_QUERY,
                variables,
                include_extensions=True,
            )
            location = data.get("location") or {}
            connection = location.get("inventoryLevels", {})
            for edge in connection.get("edges", []):
                yield edge.get("node")
            page_info = connection.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            page += 1
            if max_pages is not None and page >= max_pages:
                break
            variables["after"] = page_info.get("endCursor")

    def list_locations(
        self,
        *,
        query: Optional[str] = None,
        page_size: int = 50,
        max_pages: Optional[int] = None,
    ) -> Iterable[Dict[str, Any]]:
        variables = {"first": page_size, "after": None, "query": query}
        page = 0
        while True:
            data, _extensions = self._execute(
                LOCATIONS_PAGE_QUERY,
                variables,
                include_extensions=True,
            )
            connection = data.get("locations", {})
            for edge in connection.get("edges", []):
                yield edge.get("node")
            page_info = connection.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            page += 1
            if max_pages is not None and page >= max_pages:
                break
            variables["after"] = page_info.get("endCursor")
