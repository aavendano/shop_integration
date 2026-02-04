import sys
from unittest.mock import MagicMock, patch

# More aggressive mocking to avoid importing any shopify_client/gql stuff
sys.modules['gql'] = MagicMock()
sys.modules['gql.transport.requests'] = MagicMock()
sys.modules['gql.transport.exceptions'] = MagicMock()
sys.modules['django'] = MagicMock()
sys.modules['django.conf'] = MagicMock()
sys.modules['shopify_models.models'] = MagicMock()
sys.modules['accounts.models'] = MagicMock()
sys.modules['shopify'] = MagicMock()

# Create a mock for ShopifyGraphQLClient since we can't import it easily due to gql dependency
class MockShopifyGraphQLClient:
    def __init__(self, shop_domain, access_token, api_version):
        pass
    def get_variant_by_barcode(self, barcode):
        pass
    def activate_inventory_at_location(self, inventory_item_id, location_id):
        pass

sys.modules['shopify_client'] = MagicMock()
sys.modules['shopify_client'].ShopifyGraphQLClient = MockShopifyGraphQLClient

# Now we can safely import the function under test by patching its imports
with patch('shopify_client.ShopifyGraphQLClient', MockShopifyGraphQLClient):
    # We still need to handle the internal imports of add_location_to_variant.py
    # Since it does 'from shopify_client import ShopifyGraphQLClient' etc.
    
    # Let's mock the module where the function lives to test it in isolation if possible
    # or just use very careful patching.
    
    def test_add_location_to_variant():
        # We'll patch the imports within the function's scope by patching the modules
        with patch('shopify_client.ShopifyGraphQLClient') as MockClient:
            # We need to import it here after mocks are set
            import shopify_client.utils.add_location_to_variant as mod
            
            mock_variant = MagicMock()
            mock_variant.barcode = "123456789"
            mock_variant.id = 1

            mock_session = MagicMock()
            mock_session.site = "test-store.myshopify.com"
            mock_session.token = "test-token"
            
            with patch('accounts.models.Session.objects.first', return_value=mock_session):
                with patch('django.conf.settings') as mock_settings:
                    mock_settings.API_VERSION = "2025-10"
                    mock_settings.SHOPIFY_DEFAULT_LOCATION = "gid://shopify/Location/123"

                    client_instance = MockClient.return_value
                    client_instance.get_variant_by_barcode.return_value = {
                        "id": "gid://shopify/ProductVariant/1",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/111"}
                    }

                    # Run function
                    result = mod.add_location_to_variant(mock_variant)

                    # Assertions
                    assert result is True
                    client_instance.get_variant_by_barcode.assert_called_with("123456789")
                    client_instance.activate_inventory_at_location.assert_called_with(
                        inventory_item_id="gid://shopify/InventoryItem/111",
                        location_id="gid://shopify/Location/123"
                    )
                    print("Test passed!")

    if __name__ == "__main__":
        try:
            test_add_location_to_variant()
        except AssertionError as e:
            print(f"Test failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
