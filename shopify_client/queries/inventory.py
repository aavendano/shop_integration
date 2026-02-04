INVENTORY_ITEMS_PAGE = """
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

INVENTORY_ITEMS_PAGE_QUERY = INVENTORY_ITEMS_PAGE


LOCATION_INVENTORY_LEVELS_PAGE = """
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

LOCATION_INVENTORY_LEVELS_QUERY = LOCATION_INVENTORY_LEVELS_PAGE


LOCATIONS_PAGE_QUERY = """
query LocationsPage($first: Int!, $after: String, $query: String) {
  locations(first: $first, after: $after, query: $query) {
    edges {
      cursor
      node {
        id
        name
        isActive
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


VARIANT_INVENTORY_ITEM_ID = """
query VariantInventoryItem($id: ID!) {
  productVariant(id: $id) {
    inventoryItem {
      id
    }
  }
}
"""


INVENTORY_ITEM_UPDATE = """
mutation InventoryItemUpdate($id: ID!, $input: InventoryItemInput!) {
  inventoryItemUpdate(id: $id, input: $input) {
    inventoryItem {
      id
      unitCost {
        amount
        currencyCode
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""


INVENTORY_SET_QUANTITIES = """
mutation InventorySetQuantities($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup {
      createdAt
      reason
    }
    userErrors {
      field
      message
    }
  }
}
"""


LOCATION_BY_ID = """
query LocationById($id: ID!) {
  location(id: $id) {
    id
    name
  }
}
"""


INVENTORY_LEVELS_BY_ITEM = """
query InventoryLevels($inventoryItemId: ID!, $first: Int!, $quantityNames: [String!]!) {
  inventoryItem(id: $inventoryItemId) {
    inventoryLevels(first: $first) {
      edges {
        node {
          location {
            id
            name
          }
          quantities(names: $quantityNames) {
            name
            quantity
          }
        }
      }
    }
  }
}
"""


INVENTORY_ACTIVATE = """
mutation InventoryActivate($inventoryItemId: ID!, $locationId: ID!) {
  inventoryActivate(inventoryItemId: $inventoryItemId, locationId: $locationId) {
    inventoryLevel {
      id
      item {
        id
      }
      location {
        id
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

INVENTORY_ITEM_UPDATE_FULFILLMENT = """
mutation InventoryItemUpdateFulfillment($id: ID!, $input: InventoryItemInput!) {
  inventoryItemUpdate(id: $id, input: $input) {
    inventoryItem {
      id
      tracked
    }
    userErrors {
      field
      message
    }
  }
}
"""
