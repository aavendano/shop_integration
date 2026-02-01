from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..graphql import ShopifyGraphQLClient
from ..models import InventoryItem, InventoryLevel


LOCATIONS_PAGE_QUERY = """
query LocationsPage($first: Int!, $after: String, $query: String) {
  locations(first: $first, after: $after, query: $query) {
    edges {
      cursor
      node {
        id
        legacyResourceId
        name
        isActive
        activatable
        deactivatable
        deletable
        fulfillsOnlineOrders
        hasActiveInventory
        hasUnfulfilledOrders
        shipsInventory
        address {
          address1
          address2
          city
          country
          countryCode
          province
          provinceCode
          zip
        }
        localPickupSettingsV2 {
          pickupTime
          instructions
        }
        createdAt
        updatedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


INVENTORY_ITEMS_PAGE_QUERY = """
query InventoryItemsPage($first: Int!, $after: String, $query: String) {
  inventoryItems(first: $first, after: $after, query: $query) {
    edges {
      cursor
      node {
        id
        legacyResourceId
        sku
        tracked
        requiresShipping
        countryCodeOfOrigin
        provinceCodeOfOrigin
        harmonizedSystemCode
        countryHarmonizedSystemCodes(first: 10) {
          edges {
            node {
              harmonizedSystemCode
              countryCode
            }
          }
        }
        unitCost {
          amount
          currencyCode
        }
        locationsCount {
          count
        }
        createdAt
        updatedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


LOCATION_INVENTORY_LEVELS_QUERY = """
query LocationInventoryLevelsSince(
  $locationId: ID!
  $first: Int!
  $after: String
  $updatedAtQuery: String
  $quantityNames: [String!]!
) {
  location(id: $locationId) {
    id
    name
    inventoryLevels(first: $first, after: $after, query: $updatedAtQuery) {
      edges {
        cursor
        node {
          id
          quantities(names: $quantityNames) {
            name
            quantity
          }
          item {
            id
            sku
          }
          location {
            id
            name
          }
          createdAt
          updatedAt
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


# NOTE: Location model has been removed. Location data is now managed via .env
# def sync_locations(session, *, query=None, page_size=50, max_pages=None, throttle=True):
#     client = ShopifyGraphQLClient(session, throttle=throttle)
#     variables = {"first": page_size, "after": None, "query": query}
#     page = 0
#     synced = 0
#     while True:
#         data, _extensions = client.execute(LOCATIONS_PAGE_QUERY, variables=variables)
#         connection = data["locations"]
#         for edge in connection["edges"]:
#             synced += 1
#             _upsert_location(session, edge["node"])
#         page_info = connection["pageInfo"]
#         if not page_info["hasNextPage"]:
#             break
#         page += 1
#         if max_pages is not None and page >= max_pages:
#             break
#         variables["after"] = page_info["endCursor"]
#     return synced


def sync_inventory_items(
    session, *, query=None, page_size=50, max_pages=None, throttle=True
):
    client = ShopifyGraphQLClient(session, throttle=throttle)
    variables = {"first": page_size, "after": None, "query": query}
    page = 0
    synced = 0
    while True:
        data, _extensions = client.execute(
            INVENTORY_ITEMS_PAGE_QUERY, variables=variables
        )
        connection = data["inventoryItems"]
        for edge in connection["edges"]:
            synced += 1
            _upsert_inventory_item(session, edge["node"])
        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        page += 1
        if max_pages is not None and page >= max_pages:
            break
        variables["after"] = page_info["endCursor"]
    return synced


def sync_location_inventory_levels(
    location_gid,
    session,
    *,
    updated_at_query=None,
    page_size=50,
    max_pages=None,
    throttle=True,
    quantity_names=None,
):
    """
    Sync inventory levels for a specific location.
    
    Args:
        location_gid: The Shopify location GID (e.g., "gid://shopify/Location/89689161972")
        session: The session object
        updated_at_query: Optional query filter for updated_at
        page_size: Number of items per page
        max_pages: Maximum number of pages to fetch
        throttle: Whether to throttle API requests
        quantity_names: List of quantity names to fetch
    
    Returns:
        Number of inventory levels synced
    """
    quantity_names = quantity_names or ["available", "incoming", "on_hand"]
    client = ShopifyGraphQLClient(session, throttle=throttle)
    variables = {
        "locationId": location_gid,
        "first": page_size,
        "after": None,
        "updatedAtQuery": updated_at_query,
        "quantityNames": quantity_names,
    }
    page = 0
    synced = 0
    now = timezone.now()
    while True:
        data, _extensions = client.execute(
            LOCATION_INVENTORY_LEVELS_QUERY, variables=variables
        )
        connection = data["location"]["inventoryLevels"]
        for edge in connection["edges"]:
            synced += 1
            _upsert_inventory_level(location_gid, session, edge["node"], synced_at=now)
        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        page += 1
        if max_pages is not None and page >= max_pages:
            break
        variables["after"] = page_info["endCursor"]
    return synced


# NOTE: Location model has been removed. Location data is now managed via .env
# def _upsert_location(session, node):
#     legacy_id = node.get("legacyResourceId")
#     if legacy_id is None:
#         legacy_id = _parse_legacy_id(node.get("id"))
#     defaults = {
#         "session": session,
#         "admin_graphql_api_id": node.get("id"),
#         "name": node.get("name"),
#         "is_active": node.get("isActive") or False,
#         "activatable": node.get("activatable") or False,
#         "deactivatable": node.get("deactivatable") or False,
#         "deletable": node.get("deletable") or False,
#         "fulfills_online_orders": node.get("fulfillsOnlineOrders") or False,
#         "has_active_inventory": node.get("hasActiveInventory") or False,
#         "has_unfulfilled_orders": node.get("hasUnfulfilledOrders") or False,
#         "ships_inventory": node.get("shipsInventory") or False,
#         "address": node.get("address"),
#         "local_pickup_settings": node.get("localPickupSettingsV2"),
#         "created_at": _parse_datetime(node.get("createdAt")),
#         "updated_at": _parse_datetime(node.get("updatedAt")),
#     }
#     Location.objects.update_or_create(id=legacy_id, defaults=defaults)


def _upsert_inventory_item(session, node):
    legacy_id = node.get("legacyResourceId")
    if legacy_id is None:
        legacy_id = _parse_legacy_id(node.get("id"))
    amount, currency = InventoryItem.normalize_unit_cost(node.get("unitCost"))
    defaults = {
        "session": session,
        "admin_graphql_api_id": node.get("id"),
        "shopify_sku": node.get("sku"),
        "tracked": node.get("tracked") or False,
        "requires_shipping": node.get("requiresShipping") or False,
        "unit_cost_amount": amount,
        "unit_cost_currency": currency,
        #"locations_count": _extract_count(node.get("locationsCount")),
}
    InventoryItem.objects.update_or_create(id=legacy_id, defaults=defaults)


def _upsert_inventory_level(location_gid, session, node, *, synced_at):
    """
    Update or create an inventory level.
    
    Args:
        location_gid: The Shopify location GID (e.g., "gid://shopify/Location/89689161972")
        session: The session object
        node: The inventory level data from GraphQL
        synced_at: Timestamp of when this sync occurred
    """
    inventory_item_gid = node["item"]["id"]
    inventory_item_id = _parse_legacy_id(inventory_item_gid)
    inventory_item, _created = InventoryItem.objects.get_or_create(
        id=inventory_item_id,
        defaults={
            "session": session,
            "admin_graphql_api_id": inventory_item_gid,
            "shopify_sku": node["item"].get("sku"),
        },
    )
    level_id = _parse_legacy_id(node["id"])
    quantities = {
        quantity["name"]: quantity["quantity"]
        for quantity in node.get("quantities", [])
    }
    defaults = {
        "session": session,
        "admin_graphql_api_id": node["id"],
        "inventory_item": inventory_item,
        "location_gid": location_gid,
        "quantities": quantities,
        "source_updated_at": _parse_datetime(node.get("updatedAt")),
        "synced_at": synced_at,
        "sync_pending": False,
    }
    InventoryLevel.objects.update_or_create(id=level_id, defaults=defaults)


def _extract_count(obj):
    if not obj:
        return None
    return obj.get("count")


def _flatten_country_codes(connection):
    if not connection:
        return None
    return [edge["node"] for edge in connection.get("edges", [])]


def _parse_legacy_id(gid):
    if not gid:
        return None
    resource_part = gid.split("gid://shopify/")[-1]
    resource_part = resource_part.split("?")[0]
    parts = resource_part.split("/")
    if len(parts) >= 2:
        return int(parts[1])
    return None


def _parse_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.utc)
    return parsed
