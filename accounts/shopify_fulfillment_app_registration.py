from django.conf import settings

from shopify_client import ShopifyGraphQLClient
from shopify_client.exceptions import ShopifyClientError

SHOP_URL = settings.SHOP_ADMIN_URL
ACCESS_TOKEN = settings.SHOPIFY_ACCESS_TOKEN
WEBHOOK_URL = settings.WEBHOOK_URL

def register_fulfillment_service():
    # The callbackUrl should be the base URL. Shopify appends /fulfillment_order_notification, etc.
    # For n8n, this is typically https://your-n8n-instance.com/webhook
    callback_url = WEBHOOK_URL

    if not ACCESS_TOKEN:
        print("Error: SHOPIFY_ACCESS_TOKEN environment variable is not set.")
        return
    if not SHOP_URL:
        print("Error: SHOP_ADMIN_URL environment variable is not set.")
        return
    if not callback_url:
        print("Error: WEBHOOK_URL environment variable is not set.")
        return

    client = ShopifyGraphQLClient(
        SHOP_URL,
        ACCESS_TOKEN,
        settings.API_VERSION,
    )

    try:
        fulfillment_service = client.register_fulfillment_service(
            callback_url=callback_url,
            name="Mi Servicio Fulfillment",
            tracking_support=True,
            inventory_management=True,
        )
    except ShopifyClientError as e:
        print(f"Error registering fulfillment service: {e}")
        return

    if fulfillment_service:
        location = fulfillment_service.get("location") or {}
        location_id = location.get("id")
        if location_id:
            print(f"\n✅ Location ID: {location_id}")
            print("Guarda este ID en tu .env como FULFILLMENT_LOCATION_ID")
        else:
            print("\n⚠️ Fulfillment service created without location ID.")
    else:
        print("\n⚠️ No fulfillment service returned. Check userErrors.")
