GET_PRODUCT_BY_SKU = """
query GetProductBySku($query: String!) {
  products(first: 1, query: $query) {
    edges {
      node {
        id
        title
        handle
        description
        vendor
        productType
        tags
        status
        variants(first: 10) {
          edges {
            node {
              id
              sku
              price
              compareAtPrice
              inventoryItem {
                id
                tracked
              }
            }
          }
        }
      }
    }
  }
}
"""

GET_VARIANT_BY_BARCODE = """
query GetVariantByBarcode($query: String!) {
  productVariants(first: 1, query: $query) {
    edges {
      node {
        id
        sku
        barcode
        inventoryItem {
          id
          tracked
        }
      }
    }
  }
}
"""
