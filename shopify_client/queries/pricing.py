GET_CATALOG_BY_TITLE = """
query GetCatalog($query: String!) {
  catalogs(first: 10, query: $query) {
    edges {
      node {
        id
        title
      }
    }
  }
}
"""


GET_PRICE_LISTS = """
query GetPriceLists {
  priceLists(first: 50) {
    edges {
      node {
        id
        name
        currency
      }
    }
  }
}
"""


CREATE_CATALOG = """
mutation CreateCatalog($input: CatalogCreateInput!) {
  catalogCreate(input: $input) {
    catalog {
      id
      title
      status
    }
    userErrors {
      field
      message
    }
  }
}
"""


CREATE_PRICE_LIST = """
mutation CreatePriceList($input: PriceListCreateInput!) {
  priceListCreate(input: $input) {
    priceList {
      id
      name
      currency
    }
    userErrors {
      field
      message
    }
  }
}
"""


PRICE_LIST_FIXED_PRICES_ADD = """
mutation AddFixedPrices($priceListId: ID!, $prices: [PriceListPriceInput!]!) {
  priceListFixedPricesAdd(priceListId: $priceListId, prices: $prices) {
    prices {
      price {
        amount
        currencyCode
      }
      variant {
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
