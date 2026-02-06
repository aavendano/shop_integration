"""
Unit tests for inventory API endpoints.

Tests verify that inventory endpoints correctly handle list and reconcile operations.
"""

import pytest
import jwt
import time
from shopify_models.models import Product, Variant, InventoryItem, InventoryLevel
from api.serializers import InventoryItemSerializer
from django.test import Client
from django.urls import reverse
from accounts.models import Shop, Session


def create_jwt_token(shop_domain, client_id='test_client_id', client_secret='test_client_secret'):
    """Helper function to create a valid JWT token."""
    payload = {
        'dest': f'https://{shop_domain}',
        'aud': client_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,
    }
    
    token = jwt.encode(
        payload,
        client_secret,
        algorithm='HS256'
    )
    # Ensure token is a string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


@pytest.mark.django_db
class TestInventoryListView:
    """Test InventoryListView API endpoint."""
    
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Set up test fixtures."""
        # Mock Django settings
        monkeypatch.setenv('SHOPIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setenv('SHOPIFY_CLIENT_SECRET', 'test_client_secret')
        
        # Reload settings to pick up environment variables
        from django.conf import settings
        settings.SHOPIFY_CLIENT_ID = 'test_client_id'
        settings.SHOPIFY_CLIENT_SECRET = 'test_client_secret'
        
        # Create a test shop
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            domain='test-shop.com',
            name='Test Shop',
            currency='USD',
            client_id='test_client_id',
            client_secret='test_client_secret',
            is_authentified=True
        )
        
        self.token = create_jwt_token(self.shop.myshopify_domain)
    
    def test_inventory_list_returns_tracked_items_only(self):
        """
        Test that inventory list endpoint returns only tracked inventory items.
        Requirements: 4.1, 4.2
        """
        # Create a product and variants
        product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product'
        )
        
        # Create tracked variant
        tracked_variant = Variant.objects.create(
            product=product,
            title='Tracked',
            supplier_sku='SKU_TRACKED',
            grams=100,
            price='99.99'
        )
        
        # Create untracked variant
        untracked_variant = Variant.objects.create(
            product=product,
            title='Untracked',
            supplier_sku='SKU_UNTRACKED',
            grams=100,
            price='49.99'
        )
        
        # Create tracked inventory item
        tracked_item = InventoryItem.objects.create(
            variant=tracked_variant,
            shopify_sku='SKU_TRACKED',
            tracked=True,
            source_quantity=50
        )
        
        # Create untracked inventory item
        untracked_item = InventoryItem.objects.create(
            variant=untracked_variant,
            shopify_sku='SKU_UNTRACKED',
            tracked=False,
            source_quantity=None
        )
        
        # Make request to inventory list endpoint
        client = Client()
        response = client.get(
            '/api/admin/inventory/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Should only return tracked items
        assert data['count'] == 1
        assert len(data['results']) == 1
        assert data['results'][0]['id'] == tracked_item.id
        assert data['results'][0]['tracked'] is True


@pytest.mark.django_db
class TestInventoryReconcileView:
    """Test InventoryReconcileView API endpoint."""
    
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Set up test fixtures."""
        # Mock Django settings
        monkeypatch.setenv('SHOPIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setenv('SHOPIFY_CLIENT_SECRET', 'test_client_secret')
        monkeypatch.setenv('SHOPIFY_DEFAULT_LOCATION', 'gid://shopify/Location/123')
        
        # Reload settings to pick up environment variables
        from django.conf import settings
        settings.SHOPIFY_CLIENT_ID = 'test_client_id'
        settings.SHOPIFY_CLIENT_SECRET = 'test_client_secret'
        settings.SHOPIFY_DEFAULT_LOCATION = 'gid://shopify/Location/123'
        
        # Create a test shop
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            domain='test-shop.com',
            name='Test Shop',
            currency='USD',
            client_id='test_client_id',
            client_secret='test_client_secret',
            is_authentified=True
        )
        
        # Create a session for the shop
        self.session = Session.objects.create(
            shop=self.shop,
            token='test_token',
            site=f'https://{self.shop.myshopify_domain}'
        )
        
        self.token = create_jwt_token(self.shop.myshopify_domain)
    
    def test_inventory_reconcile_returns_success(self):
        """
        Test that inventory reconcile endpoint returns success response.
        Requirements: 4.5, 4.6, 4.7
        """
        from unittest.mock import patch, MagicMock
        
        # Create a product and inventory item
        product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product'
        )
        
        variant = Variant.objects.create(
            product=product,
            title='Default',
            supplier_sku='SKU123',
            grams=100,
            price='99.99'
        )
        
        inventory_item = InventoryItem.objects.create(
            variant=variant,
            shopify_sku='SKU123',
            tracked=True,
            source_quantity=50,
            shopify_id='123'
        )
        
        # Create an inventory level
        InventoryLevel.objects.create(
            inventory_item=inventory_item,
            location_gid='gid://shopify/Location/123',
            sync_pending=False
        )
        
        # Mock the Shopify client at the import location
        with patch('shopify_client.ShopifyGraphQLClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.set_inventory_quantities.return_value = []  # No errors
            
            # Make request to reconcile endpoint
            client = Client()
            response = client.post(
                '/api/admin/inventory/reconcile/',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert 'success' in data
        assert 'reconciled_count' in data
        assert 'message' in data
        assert data['success'] is True
        assert data['reconciled_count'] >= 0
    
    def test_inventory_reconcile_response_structure(self):
        """
        Test that inventory reconcile endpoint returns correct response structure.
        Requirements: 4.5, 4.6, 4.7
        """
        # Make request to reconcile endpoint
        client = Client()
        response = client.post(
            '/api/admin/inventory/reconcile/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert 'success' in data
        assert 'reconciled_count' in data
        assert 'message' in data
        assert isinstance(data['success'], bool)
        assert isinstance(data['reconciled_count'], int)
        assert isinstance(data['message'], str)
    
    def test_inventory_reconcile_counts_tracked_items_only(self):
        """
        Test that inventory reconcile only counts tracked inventory items.
        Requirements: 4.5, 4.6
        """
        from unittest.mock import patch, MagicMock
        
        # Create a product
        product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product'
        )
        
        # Create tracked variant
        tracked_variant = Variant.objects.create(
            product=product,
            title='Tracked',
            supplier_sku='SKU_TRACKED',
            grams=100,
            price='99.99'
        )
        
        # Create untracked variant
        untracked_variant = Variant.objects.create(
            product=product,
            title='Untracked',
            supplier_sku='SKU_UNTRACKED',
            grams=100,
            price='49.99'
        )
        
        # Create tracked inventory item
        tracked_item = InventoryItem.objects.create(
            variant=tracked_variant,
            shopify_sku='SKU_TRACKED',
            tracked=True,
            source_quantity=50,
            shopify_id='123'
        )
        
        # Create untracked inventory item
        untracked_item = InventoryItem.objects.create(
            variant=untracked_variant,
            shopify_sku='SKU_UNTRACKED',
            tracked=False,
            source_quantity=None,
            shopify_id='124'
        )
        
        # Create inventory levels
        InventoryLevel.objects.create(
            inventory_item=tracked_item,
            location_gid='gid://shopify/Location/123',
            sync_pending=False
        )
        
        InventoryLevel.objects.create(
            inventory_item=untracked_item,
            location_gid='gid://shopify/Location/123',
            sync_pending=False
        )
        
        # Mock the Shopify client
        with patch('shopify_client.ShopifyGraphQLClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.set_inventory_quantities.return_value = []  # No errors
            
            # Make request to reconcile endpoint
            client = Client()
            response = client.post(
                '/api/admin/inventory/reconcile/',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Should only count tracked items
        assert data['reconciled_count'] == 1
    
    def test_inventory_reconcile_skips_items_without_quantity(self):
        """
        Test that inventory reconcile skips items without source_quantity.
        Requirements: 4.5, 4.6
        """
        # Create a product
        product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product'
        )
        
        # Create variant
        variant = Variant.objects.create(
            product=product,
            title='Default',
            supplier_sku='SKU123',
            grams=100,
            price='99.99'
        )
        
        # Create inventory item without source_quantity
        inventory_item = InventoryItem.objects.create(
            variant=variant,
            shopify_sku='SKU123',
            tracked=True,
            source_quantity=None,
            shopify_id='125'
        )
        
        # Create an inventory level
        InventoryLevel.objects.create(
            inventory_item=inventory_item,
            location_gid='gid://shopify/Location/123',
            sync_pending=False
        )
        
        # Make request to reconcile endpoint
        client = Client()
        response = client.post(
            '/api/admin/inventory/reconcile/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Should not count items without quantity
        assert data['reconciled_count'] == 0
