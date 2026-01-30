import os
import requests
import json

SHOP_URL = os.getenv('SHOPIFY_SHOP_URL', 'tu-tienda.myshopify.com')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://n8n.tudominio.com/')

def register_fulfillment_service():
    # The callbackUrl should be the base URL. Shopify appends /fulfillment_order_notification, etc.
    # For n8n, this is typically https://your-n8n-instance.com/webhook
    callback_url = WEBHOOK_URL

    mutation = f'''
    mutation {{
      fulfillmentServiceCreate(
        name: "Mi Servicio Fulfillment"
        callbackUrl: "{callback_url}"
        trackingSupport: true
        inventoryManagement: true
      ) {{
        fulfillmentService {{
          id
          serviceName
          location {{
            id
            name
          }}
        }}
        userErrors {{
          field
          message
        }}
      }}
    }}
    '''

    if not ACCESS_TOKEN:
        print("Error: SHOPIFY_ACCESS_TOKEN environment variable is not set.")
        return

    url = f'https://{SHOP_URL}/admin/api/2025-01/graphql.json'
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': ACCESS_TOKEN
    }

    try:
        response = requests.post(
            url,
            json={'query': mutation},
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        print(json.dumps(result, indent=2))

        # Guardar location_id para uso posterior
        data = result.get('data', {})
        if data and data.get('fulfillmentServiceCreate', {}).get('fulfillmentService'):
            location_id = data['fulfillmentServiceCreate']['fulfillmentService']['location']['id']
            print(f"\n✅ Location ID: {location_id}")
            print("Guarda este ID en tu .env como FULFILLMENT_LOCATION_ID")
        else:
             print("\n⚠️ No fulfillment service returned. Check userErrors.")

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")

