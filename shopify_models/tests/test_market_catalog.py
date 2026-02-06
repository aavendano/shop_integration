"""
Tests for Market, Catalog, Publication, and PriceList models and synchronization.
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from shopify_models.models import Market, Publication, PriceList, Catalog, Product
from shopify_models.sync import (
    sync_market,
    sync_publication,
    sync_price_list,
    sync_catalog,
    sync_product_publication
)


class MarketModelTest(TestCase):
    """Test Market model"""
    
    def test_market_creation(self):
        """Test creating a Market instance"""
        market = Market.objects.create(
            name="United States",
            handle="us",
            enabled=True,
            primary=True,
            currency="USD"
        )
        self.assertEqual(market.name, "United States")
        self.assertEqual(market.handle, "us")
        self.assertTrue(market.enabled)
        self.assertEqual(str(market), "United States")


class PublicationModelTest(TestCase):
    """Test Publication model"""
    
    def test_publication_creation(self):
        """Test creating a Publication instance"""
        publication = Publication.objects.create(auto_publish=False)
        self.assertFalse(publication.auto_publish)
        self.assertIn("Publication", str(publication))


class PriceListModelTest(TestCase):
    """Test PriceList model"""
    
    def test_price_list_creation(self):
        """Test creating a PriceList instance"""
        price_list = PriceList.objects.create(
            name="US Pricing",
            currency="USD"
        )
        self.assertEqual(price_list.name, "US Pricing")
        self.assertEqual(price_list.currency, "USD")
        self.assertEqual(str(price_list), "US Pricing")


class CatalogModelTest(TestCase):
    """Test Catalog model"""
    
    def test_catalog_creation(self):
        """Test creating a Catalog instance"""
        market = Market.objects.create(
            name="United States",
            handle="us",
            currency="USD"
        )
        publication = Publication.objects.create(auto_publish=False)
        price_list = PriceList.objects.create(
            name="US Pricing",
            currency="USD"
        )
        
        catalog = Catalog.objects.create(
            title="US Catalog",
            status="ACTIVE",
            market=market,
            publication=publication,
            price_list=price_list
        )
        
        self.assertEqual(catalog.title, "US Catalog")
        self.assertEqual(catalog.status, "ACTIVE")
        self.assertEqual(catalog.market, market)
        self.assertEqual(str(catalog), "US Catalog")


class MarketSyncTest(TestCase):
    """Test Market synchronization"""
    
    @patch('shopify_models.sync.get_shopify_client')
    def test_sync_market_create(self, mock_get_client):
        """Test syncing a new market to Shopify"""
        # Mock the GraphQL client
        mock_client = Mock()
        mock_client._execute.return_value = (
            {
                "marketCreate": {
                    "market": {
                        "id": "gid://shopify/Market/123",
                        "name": "United States",
                        "handle": "us"
                    },
                    "userErrors": []
                }
            },
            {}  # extensions
        )
        mock_get_client.return_value = mock_client
        
        # Create market
        market = Market.objects.create(
            name="United States",
            handle="us",
            enabled=True,
            currency="USD"
        )
        
        # Sync
        result = sync_market(market)
        
        # Verify
        self.assertEqual(market.shopify_id, "gid://shopify/Market/123")
        mock_client._execute.assert_called_once()



class CatalogSyncTest(TestCase):
    """Test Catalog synchronization"""
    
    @patch('shopify_models.sync.sync_publication')
    @patch('shopify_models.sync.sync_price_list')
    @patch('shopify_models.sync.get_shopify_client')
    def test_sync_catalog_with_dependencies(self, mock_get_client, mock_sync_price_list, mock_sync_publication):
        """Test syncing a catalog with automatic dependency creation"""
        # Mock the GraphQL client
        mock_client = Mock()
        mock_client._execute.return_value = (
            {
                "catalogCreate": {
                    "catalog": {
                        "id": "gid://shopify/Catalog/456",
                        "title": "US Catalog",
                        "status": "ACTIVE"
                    },
                    "userErrors": []
                }
            },
            {}  # extensions
        )
        mock_get_client.return_value = mock_client
        
        # Mock dependency syncs
        def mock_pub_sync(pub):
            pub.shopify_id = "gid://shopify/Publication/789"
            pub.save()
            
        def mock_price_sync(price):
            price.shopify_id = "gid://shopify/PriceList/101"
            price.save()
            
        mock_sync_publication.side_effect = mock_pub_sync
        mock_sync_price_list.side_effect = mock_price_sync
        
        # Create market
        market = Market.objects.create(
            name="United States",
            handle="us",
            currency="USD",
            shopify_id="gid://shopify/Market/123"
        )
        
        # Create catalog without dependencies
        catalog = Catalog.objects.create(
            title="US Catalog",
            status="ACTIVE",
            market=market
        )
        
        # Sync with dependency creation
        result = sync_catalog(catalog, create_dependencies=True)
        
        # Verify dependencies were created
        self.assertIsNotNone(catalog.publication)
        self.assertIsNotNone(catalog.price_list)
        self.assertEqual(catalog.publication.shopify_id, "gid://shopify/Publication/789")
        self.assertEqual(catalog.price_list.shopify_id, "gid://shopify/PriceList/101")
        
        # Verify catalog was synced
        self.assertEqual(catalog.shopify_id, "gid://shopify/Catalog/456")



class ProductCatalogTest(TestCase):
    """Test Product-Catalog relationship"""
    
    @patch('shopify_models.sync.get_shopify_client')
    def test_product_catalog_availability(self, mock_get_client):
        """Test publishing/unpublishing product to catalog"""
        # Mock the GraphQL client
        mock_client = Mock()
        mock_client._execute.return_value = (
            {
                "publishablePublish": {
                    "publishable": {
                        "id": "gid://shopify/Product/999",
                        "title": "Test Product"
                    },
                    "userErrors": []
                }
            },
            {}  # extensions
        )
        mock_get_client.return_value = mock_client
        
        # Create product
        product = Product.objects.create(
            title="Test Product",
            handle="test-product",
            product_type="Test",
            shopify_id="gid://shopify/Product/999"
        )
        
        # Create catalog with publication
        publication = Publication.objects.create(
            auto_publish=False,
            shopify_id="gid://shopify/Publication/789"
        )
        catalog = Catalog.objects.create(
            title="Test Catalog",
            status="ACTIVE",
            publication=publication
        )
        
        # Publish product to catalog
        product.update_catalog_availability(catalog, is_available=True)
        
        # Verify
        self.assertIn(catalog, product.catalogs.all())
        mock_client._execute.assert_called()

