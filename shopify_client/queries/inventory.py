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
