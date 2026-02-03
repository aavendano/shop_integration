FULFILLMENT_SERVICE_CREATE = """
mutation FulfillmentServiceCreate(
  $callbackUrl: URL!
  $name: String!
  $trackingSupport: Boolean!
  $inventoryManagement: Boolean!
) {
  fulfillmentServiceCreate(
    name: $name
    callbackUrl: $callbackUrl
    trackingSupport: $trackingSupport
    inventoryManagement: $inventoryManagement
  ) {
    fulfillmentService {
      id
      serviceName
      location {
        id
        name
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""
