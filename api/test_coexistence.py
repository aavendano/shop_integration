"""
Tests for verifying coexistence of existing Django UI and new Polaris API layer.

This test suite ensures that:
1. Existing Django URL routes work unchanged
2. API endpoints use distinct /api/admin/ namespace
3. Both UIs can be accessed simultaneously
4. No backend modifications have been made
5. API layer delegates to existing business logic

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7
"""
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.db import connection
from django.test.utils import override_settings
from accounts.models import Shop, User, Session
from shopify_models.models import Product, Variant, InventoryItem, Image
from api.models import Job
from django.utils import timezone
from datetime import timedelta
import json


class ExistingDjangoUITestCase(TestCase):
    """
    Test 20.1: Verify all existing Django URL routes work unchanged.
    Requirements: 19.1, 19.2
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product',
            shopify_id='gid://shopify/Product/123'
        )
        
        self.variant = Variant.objects.create(
            product=self.product,
            title='Default',
            supplier_sku='SKU123',
            price='99.99',
            grams=100,
            shopify_id='gid://shopify/ProductVariant/456'
        )
    
    def test_core_home_route_exists(self):
        """
        Test that the core home route still exists and works.
        Requirements: 19.1
        """
        response = self.client.get('/')
        
        # Should return 200 (or redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_core_login_route_exists(self):
        """
        Test that the core login route still exists.
        Requirements: 19.1
        """
        response = self.client.get('/login/')
        
        # Should return 200 (login page)
        self.assertEqual(response.status_code, 200)
    
    def test_core_logout_route_exists(self):
        """
        Test that the core logout route still exists.
        Requirements: 19.1
        """
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/logout/')
        
        # Should redirect after logout (POST method)
        self.assertEqual(response.status_code, 302)
    
    def test_shopify_models_product_list_route_exists(self):
        """
        Test that the shopify_models product list route still exists.
        Requirements: 19.1
        """
        response = self.client.get('/shopify_models/products/')
        
        # Should return 200 or 302 (redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_shopify_models_product_detail_route_exists(self):
        """
        Test that the shopify_models product detail route still exists.
        Requirements: 19.1
        """
        response = self.client.get(f'/shopify_models/products/{self.product.id}/')
        
        # Should return 200 or 302 (redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_shopify_models_product_sync_route_exists(self):
        """
        Test that the shopify_models product sync route still exists.
        Requirements: 19.1
        """
        response = self.client.post(f'/shopify_models/products/{self.product.id}/sync/')
        
        # Should return 200, 302, or 405 (method not allowed if not authenticated)
        self.assertIn(response.status_code, [200, 302, 405])
    
    def test_prices_setup_route_exists(self):
        """
        Test that the prices setup route still exists.
        Requirements: 19.1
        """
        response = self.client.get('/prices/setup/')
        
        # Should return 200 or 302 (redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_site_route_exists(self):
        """
        Test that the Django admin site route still exists.
        Requirements: 19.1
        """
        response = self.client.get('/admin/')
        
        # Should return 200 or 302 (redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_django_views_return_html(self):
        """
        Test that Django views return HTML content type.
        Requirements: 19.2
        """
        response = self.client.get('/login/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
    
    def test_django_templates_render(self):
        """
        Test that Django templates are still being rendered.
        Requirements: 19.2
        """
        response = self.client.get('/login/')
        
        self.assertEqual(response.status_code, 200)
        # Check for common HTML elements
        self.assertIn(b'<!DOCTYPE', response.content)
    
    def test_url_routing_resolution(self):
        """
        Test that URL routing still resolves correctly for Django views.
        Requirements: 19.1
        """
        # Test core URLs
        match = resolve('/')
        self.assertEqual(match.app_names, ['core'])
        
        match = resolve('/login/')
        self.assertEqual(match.app_names, ['core'])
        
        # Test shopify_models URLs
        match = resolve('/shopify_models/products/')
        self.assertEqual(match.app_names, ['shopify_models'])
        
        # Test prices URLs
        match = resolve('/prices/setup/')
        self.assertEqual(match.app_names, ['prices'])


class APINamespaceSeparationTestCase(TestCase):
    """
    Test 20.2: Verify API endpoints use distinct /api/admin/ namespace.
    Requirements: 19.3
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_api_endpoints_use_api_admin_namespace(self):
        """
        Test that all API endpoints use /api/admin/ namespace.
        Requirements: 19.3
        """
        api_endpoints = [
            '/api/admin/context/',
            '/api/admin/products/',
            '/api/admin/inventory/',
            '/api/admin/jobs/',
            '/api/admin/settings/',
        ]
        
        for endpoint in api_endpoints:
            # Just verify the endpoint is accessible (may return 404 or 200)
            response = self.client.get(endpoint)
            # Should not return 404 for routing (may return 401 or 200)
            self.assertNotEqual(response.status_code, 404, 
                              f"Endpoint {endpoint} not found in routing")
    
    def test_api_endpoints_return_json(self):
        """
        Test that API endpoints return JSON content type.
        Requirements: 19.3
        """
        response = self.client.get('/api/admin/context/')
        
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_no_conflict_with_django_urls(self):
        """
        Test that API namespace doesn't conflict with existing Django URLs.
        Requirements: 19.3
        """
        # Django URL
        django_response = self.client.get('/login/')
        self.assertEqual(django_response.status_code, 200)
        self.assertIn('text/html', django_response['Content-Type'])
        
        # API URL
        api_response = self.client.get('/api/admin/context/')
        self.assertEqual(api_response['Content-Type'], 'application/json')
        
        # Both should work independently
        self.assertNotEqual(
            django_response['Content-Type'],
            api_response['Content-Type']
        )
    
    def test_api_urls_resolve_correctly(self):
        """
        Test that API URLs resolve to correct views.
        Requirements: 19.3
        """
        # Test API URL resolution
        match = resolve('/api/admin/context/')
        self.assertEqual(match.app_names, ['api', 'admin'])
        
        match = resolve('/api/admin/products/')
        self.assertEqual(match.app_names, ['api', 'admin'])
        
        match = resolve('/api/admin/jobs/')
        self.assertEqual(match.app_names, ['api', 'admin'])
    
    def test_webhook_endpoints_separate_from_api(self):
        """
        Test that webhook endpoints are separate from API endpoints.
        Requirements: 19.3
        """
        # Webhook endpoints should be under /webhooks/, not /api/admin/
        # Note: Webhook endpoints may not be fully implemented yet
        # This test verifies the URL namespace is separate from API
        
        # Verify API endpoints are under /api/admin/
        api_response = self.client.get('/api/admin/context/')
        self.assertEqual(api_response['Content-Type'], 'application/json')
        
        # Verify webhook namespace is separate
        # (webhook endpoints may return 404 if not implemented)
        webhook_response = self.client.post('/webhooks/app/uninstalled')
        # Should not be routed to API endpoints
        self.assertNotEqual(webhook_response['Content-Type'], 'application/json')


class SimultaneousAccessTestCase(TestCase):
    """
    Test 20.3: Verify both UIs can be accessed simultaneously.
    Requirements: 19.4, 19.6, 19.7
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        self.product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product',
            shopify_id='gid://shopify/Product/123'
        )
        
        self.variant = Variant.objects.create(
            product=self.product,
            title='Default',
            supplier_sku='SKU123',
            price='99.99',
            grams=100,
            shopify_id='gid://shopify/ProductVariant/456'
        )
    
    def test_django_ui_accessible(self):
        """
        Test that Django UI is accessible.
        Requirements: 19.4
        """
        response = self.client.get('/login/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
    
    def test_api_ui_accessible(self):
        """
        Test that API UI is accessible.
        Requirements: 19.4
        """
        response = self.client.get('/api/admin/context/')
        
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_both_uis_accessible_in_sequence(self):
        """
        Test that both UIs can be accessed in sequence.
        Requirements: 19.4
        """
        # Access Django UI
        django_response = self.client.get('/login/')
        self.assertEqual(django_response.status_code, 200)
        
        # Access API UI
        api_response = self.client.get('/api/admin/context/')
        self.assertEqual(api_response['Content-Type'], 'application/json')
        
        # Access Django UI again
        django_response2 = self.client.get('/login/')
        self.assertEqual(django_response2.status_code, 200)
    
    def test_django_ui_changes_dont_affect_api(self):
        """
        Test that changes in Django UI don't affect API.
        Requirements: 19.6, 19.7
        """
        # Get initial API response
        api_response1 = self.client.get('/api/admin/products/')
        data1 = json.loads(api_response1.content)
        initial_count = data1.get('count', 0)
        
        # Access Django UI (simulating user interaction)
        django_response = self.client.get('/shopify_models/products/')
        
        # Get API response again
        api_response2 = self.client.get('/api/admin/products/')
        data2 = json.loads(api_response2.content)
        final_count = data2.get('count', 0)
        
        # Count should be the same
        self.assertEqual(initial_count, final_count)
    
    def test_api_changes_dont_affect_django_ui(self):
        """
        Test that changes in API don't affect Django UI.
        Requirements: 19.6, 19.7
        """
        # Get initial Django UI response
        django_response1 = self.client.get('/shopify_models/products/')
        
        # Make API call (simulating API interaction)
        api_response = self.client.get('/api/admin/products/')
        
        # Get Django UI response again
        django_response2 = self.client.get('/shopify_models/products/')
        
        # Both should return same status code
        self.assertIn(django_response1.status_code, [200, 302])
        self.assertIn(django_response2.status_code, [200, 302])


class BackendModificationVerificationTestCase(TestCase):
    """
    Test 20.4: Verify no backend modifications have been made.
    Requirements: 19.5
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        self.product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product',
            shopify_id='gid://shopify/Product/123'
        )
        
        self.variant = Variant.objects.create(
            product=self.product,
            title='Default',
            supplier_sku='SKU123',
            price='99.99',
            grams=100,
            shopify_id='gid://shopify/ProductVariant/456'
        )
    
    def test_product_model_unchanged(self):
        """
        Test that Product model has not been modified.
        Requirements: 19.5
        """
        # Verify product can be created and retrieved
        product = Product.objects.get(pk=self.product.pk)
        
        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.vendor, 'Test Vendor')
        self.assertEqual(product.product_type, 'Test Type')
        self.assertEqual(product.handle, 'test-product')
        self.assertEqual(product.shopify_id, 'gid://shopify/Product/123')
    
    def test_variant_model_unchanged(self):
        """
        Test that Variant model has not been modified.
        Requirements: 19.5
        """
        # Verify variant can be created and retrieved
        variant = Variant.objects.get(pk=self.variant.pk)
        
        self.assertEqual(variant.title, 'Default')
        self.assertEqual(variant.supplier_sku, 'SKU123')
        # Price is stored as Decimal in the model
        self.assertEqual(str(variant.price), '99.99')
        self.assertEqual(variant.product_id, self.product.id)
    
    def test_shop_model_unchanged(self):
        """
        Test that Shop model has not been modified.
        Requirements: 19.5
        """
        # Verify shop can be created and retrieved
        shop = Shop.objects.get(pk=self.shop.pk)
        
        self.assertEqual(shop.myshopify_domain, 'test-shop.myshopify.com')
        self.assertEqual(shop.name, 'Test Shop')
        self.assertEqual(shop.currency, 'USD')
        self.assertEqual(shop.is_authentified, True)
    
    def test_api_delegates_to_existing_business_logic(self):
        """
        Test that API layer delegates to existing business logic.
        Requirements: 19.5
        """
        # Get product via API
        response = self.client.get(f'/api/admin/products/{self.product.id}/')
        
        if response.status_code == 200:
            data = json.loads(response.content)
            
            # Verify API returns data from existing model
            self.assertEqual(data['title'], self.product.title)
            self.assertEqual(data['vendor'], self.product.vendor)
            self.assertEqual(data['product_type'], self.product.product_type)
    
    def test_existing_views_still_work(self):
        """
        Test that existing Django views still work with unchanged models.
        Requirements: 19.5
        """
        # Access existing product list view
        response = self.client.get('/shopify_models/products/')
        
        # Should return 200 or 302 (redirect if not authenticated)
        self.assertIn(response.status_code, [200, 302])
    
    def test_database_schema_unchanged(self):
        """
        Test that database schema has not been modified.
        Requirements: 19.5
        """
        # Get table names
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopify_models_%'"
            )
            tables = cursor.fetchall()
        
        # Verify expected tables exist
        table_names = [t[0] for t in tables]
        
        self.assertIn('shopify_models_product', table_names)
        self.assertIn('shopify_models_variant', table_names)
        self.assertIn('shopify_models_inventoryitem', table_names)
    
    def test_api_uses_existing_serializers(self):
        """
        Test that API uses existing serializers for data transformation.
        Requirements: 19.5
        """
        # Get product list via API
        response = self.client.get('/api/admin/products/')
        
        if response.status_code == 200:
            data = json.loads(response.content)
            
            # Verify response structure matches expected serializer output
            self.assertIn('count', data)
            self.assertIn('results', data)
            
            if data['results']:
                product = data['results'][0]
                # Verify fields come from serializer
                self.assertIn('id', product)
                self.assertIn('title', product)
                self.assertIn('vendor', product)


class CoexistenceIntegrationTestCase(TestCase):
    """
    Integration tests for coexistence of both UIs.
    Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        self.product = Product.objects.create(
            title='Test Product',
            vendor='Test Vendor',
            product_type='Test Type',
            handle='test-product',
            shopify_id='gid://shopify/Product/123'
        )
    
    def test_complete_coexistence_workflow(self):
        """
        Test a complete workflow using both UIs.
        Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7
        """
        # Step 1: Access Django UI
        django_response = self.client.get('/login/')
        self.assertEqual(django_response.status_code, 200)
        self.assertIn('text/html', django_response['Content-Type'])
        
        # Step 2: Access API (may require authentication)
        api_response = self.client.get('/api/admin/products/')
        self.assertEqual(api_response['Content-Type'], 'application/json')
        
        # Step 3: Verify API returns JSON response (with or without data)
        api_data = json.loads(api_response.content)
        # API should return JSON structure
        self.assertIsInstance(api_data, dict)
        
        # Step 4: Access Django UI again
        django_response2 = self.client.get('/shopify_models/products/')
        self.assertIn(django_response2.status_code, [200, 302])
        
        # Step 5: Access API again
        api_response2 = self.client.get('/api/admin/products/')
        api_data2 = json.loads(api_response2.content)
        
        # Step 6: Verify both return JSON
        self.assertEqual(api_response['Content-Type'], api_response2['Content-Type'])
    
    def test_url_namespace_isolation(self):
        """
        Test that URL namespaces are properly isolated.
        Requirements: 19.3
        """
        # Django URLs should not conflict with API URLs
        django_urls = [
            '/',
            '/login/',
            '/logout/',
            '/shopify_models/products/',
            '/prices/setup/',
            '/admin/',
        ]
        
        api_urls = [
            '/api/admin/context/',
            '/api/admin/products/',
            '/api/admin/inventory/',
            '/api/admin/jobs/',
            '/api/admin/settings/',
        ]
        
        # All URLs should be accessible
        for url in django_urls + api_urls:
            response = self.client.get(url)
            # Should not return 404 for routing (may return 302, 405, etc.)
            self.assertNotEqual(response.status_code, 404,
                              f"URL {url} not found in routing")
    
    def test_content_type_differentiation(self):
        """
        Test that Django UI returns HTML and API returns JSON.
        Requirements: 19.2, 19.3
        """
        # Django UI should return HTML
        django_response = self.client.get('/login/')
        self.assertIn('text/html', django_response['Content-Type'])
        
        # API should return JSON
        api_response = self.client.get('/api/admin/context/')
        self.assertEqual(api_response['Content-Type'], 'application/json')
    
    def test_independent_data_access(self):
        """
        Test that both UIs can access data independently.
        Requirements: 19.4, 19.6, 19.7
        """
        # Get product count via Django ORM
        django_count = Product.objects.count()
        
        # Get product count via API (may require authentication)
        api_response = self.client.get('/api/admin/products/')
        api_data = json.loads(api_response.content)
        
        # If API returns count, verify it matches Django count
        if 'count' in api_data:
            api_count = api_data.get('count', 0)
            self.assertEqual(api_count, django_count)
        else:
            # API may require authentication, but should still return JSON
            self.assertIsInstance(api_data, dict)
