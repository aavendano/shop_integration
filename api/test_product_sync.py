"""
Tests for the Product Sync API endpoint.
"""
from django.test import TestCase, Client
from shopify_models.models import Product, Variant
from accounts.models import Shop, Session
from unittest.mock import patch, MagicMock
import json


class ProductSyncViewTestCase(TestCase):
    """Test the product sync API endpoint."""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test shop
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        # Create a test session
        self.session = Session.objects.create(
            shop=self.shop,
            token='test_token',
            site='https://test-shop.myshopify.com'
        )
        
        # Create a test product
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            vendor='Test Vendor',
            product_type='Test Type',
            tags='test, product',
            handle='test-product',
            shopify_id=None  # Not synced yet
        )
        
        # Create a variant for the product
        self.variant = Variant.objects.create(
            product=self.product,
            title='Default',
            supplier_sku='TEST-SKU-001',
            price='99.99',
            position=1,
            grams=100  # Required field
        )
        
        self.url = f'/api/admin/products/{self.product.id}/sync/'
    
    def test_product_not_found(self):
        """
        Test that sync endpoint returns 404 for non-existent product.
        Requirements: 3.8
        """
        url = '/api/admin/products/99999/sync/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], 'Product not found')
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_successful_sync(self, mock_export):
        """
        Test successful product sync returns 200 with sync results.
        Requirements: 3.8, 3.9, 3.10
        """
        # Mock the export_to_shopify method to avoid actual Shopify API calls
        mock_export.return_value = None
        
        # Update product to simulate successful sync
        def side_effect():
            self.product.shopify_id = '12345678'
            self.product.save()
        
        mock_export.side_effect = side_effect
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('success', data)
        self.assertIn('message', data)
        self.assertIn('synced_at', data)
        
        # Verify response values
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Product synchronized successfully')
        self.assertIsNotNone(data['synced_at'])
        
        # Verify export_to_shopify was called
        mock_export.assert_called_once()
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_sync_failure(self, mock_export):
        """
        Test that sync failure returns 500 with error details.
        Requirements: 3.8, 3.11
        """
        # Mock the export_to_shopify method to raise an exception
        error_message = 'Shopify API error: Product not found'
        mock_export.side_effect = Exception(error_message)
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('success', data)
        self.assertIn('message', data)
        self.assertIn('error', data)
        
        # Verify response values
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Failed to sync product')
        self.assertEqual(data['error'], error_message)
        
        # Verify export_to_shopify was called
        mock_export.assert_called_once()
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_sync_delegates_to_business_logic(self, mock_export):
        """
        Test that sync endpoint delegates to existing Product.export_to_shopify() method.
        Requirements: 3.9
        
        This validates Property 11: Business Logic Delegation
        """
        mock_export.return_value = None
        
        response = self.client.post(self.url)
        
        # Verify the business logic method was called
        mock_export.assert_called_once()
        
        # Verify no duplication - the endpoint should only call the method,
        # not implement its own sync logic
        self.assertEqual(response.status_code, 200)
    
    def test_sync_endpoint_only_accepts_post(self):
        """
        Test that sync endpoint only accepts POST requests.
        """
        # GET should not be allowed
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # PUT should not be allowed
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 405)
        
        # DELETE should not be allowed
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 405)


class ProductBulkSyncViewTestCase(TestCase):
    """Test the product bulk sync API endpoint."""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test shop
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            name='Test Shop',
            currency='USD',
            is_authentified=True,
            domain='test-shop.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        
        # Create a test session
        self.session = Session.objects.create(
            shop=self.shop,
            token='test_token',
            site='https://test-shop.myshopify.com'
        )
        
        # Create multiple test products
        self.products = []
        for i in range(3):
            product = Product.objects.create(
                title=f'Test Product {i+1}',
                description=f'Test Description {i+1}',
                vendor='Test Vendor',
                product_type='Test Type',
                tags='test, product',
                handle=f'test-product-{i+1}',
                shopify_id=None
            )
            
            # Create a variant for each product
            Variant.objects.create(
                product=product,
                title='Default',
                supplier_sku=f'TEST-SKU-{i+1:03d}',
                price='99.99',
                position=1,
                grams=100
            )
            
            self.products.append(product)
        
        self.url = '/api/admin/products/bulk-sync/'
    
    def test_missing_product_ids(self):
        """
        Test that bulk sync returns 400 when product_ids is missing.
        Requirements: 3.12, 3.13
        """
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], 'product_ids array cannot be empty')
    
    def test_invalid_product_ids_format(self):
        """
        Test that bulk sync returns 400 when product_ids is not an array.
        Requirements: 3.12, 3.13
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': 'not-an-array'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], 'product_ids must be an array')
    
    def test_empty_product_ids_array(self):
        """
        Test that bulk sync returns 400 when product_ids array is empty.
        Requirements: 3.12, 3.13
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': []}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], 'product_ids array cannot be empty')
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_successful_bulk_sync(self, mock_export):
        """
        Test successful bulk sync of multiple products.
        Requirements: 3.12, 3.13, 3.14
        """
        # Mock the export_to_shopify method
        mock_export.return_value = None
        
        product_ids = [p.id for p in self.products]
        
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': product_ids}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('success_count', data)
        self.assertIn('error_count', data)
        self.assertIn('results', data)
        
        # Verify all products synced successfully
        self.assertEqual(data['success_count'], 3)
        self.assertEqual(data['error_count'], 0)
        self.assertEqual(len(data['results']), 3)
        
        # Verify each result
        for i, result in enumerate(data['results']):
            self.assertIn('id', result)
            self.assertIn('success', result)
            self.assertEqual(result['id'], product_ids[i])
            self.assertTrue(result['success'])
            self.assertNotIn('error', result)
        
        # Verify export_to_shopify was called for each product
        self.assertEqual(mock_export.call_count, 3)
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_bulk_sync_with_mixed_results(self, mock_export):
        """
        Test bulk sync with some successes and some failures.
        Requirements: 3.12, 3.13, 3.14
        
        This validates Property 8: Bulk Operation Completeness
        """
        # Mock export_to_shopify to fail for the second product
        def side_effect():
            if mock_export.call_count == 2:
                raise Exception('Sync failed for product 2')
        
        mock_export.side_effect = side_effect
        
        product_ids = [p.id for p in self.products]
        
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': product_ids}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify aggregated counts
        self.assertEqual(data['success_count'], 2)
        self.assertEqual(data['error_count'], 1)
        self.assertEqual(len(data['results']), 3)
        
        # Verify first product succeeded
        self.assertEqual(data['results'][0]['id'], product_ids[0])
        self.assertTrue(data['results'][0]['success'])
        
        # Verify second product failed
        self.assertEqual(data['results'][1]['id'], product_ids[1])
        self.assertFalse(data['results'][1]['success'])
        self.assertIn('error', data['results'][1])
        self.assertEqual(data['results'][1]['error'], 'Sync failed for product 2')
        
        # Verify third product succeeded
        self.assertEqual(data['results'][2]['id'], product_ids[2])
        self.assertTrue(data['results'][2]['success'])
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_bulk_sync_with_nonexistent_product(self, mock_export):
        """
        Test bulk sync handles non-existent product IDs gracefully.
        Requirements: 3.12, 3.13, 3.14
        """
        # Mock the export method for valid products
        mock_export.return_value = None
        
        product_ids = [self.products[0].id, 99999, self.products[1].id]
        
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': product_ids}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify the non-existent product is marked as error
        self.assertEqual(data['error_count'], 1)
        self.assertEqual(len(data['results']), 3)
        
        # Check the middle result (non-existent product)
        self.assertEqual(data['results'][1]['id'], 99999)
        self.assertFalse(data['results'][1]['success'])
        self.assertEqual(data['results'][1]['error'], 'Product not found')
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_bulk_sync_with_invalid_id_format(self, mock_export):
        """
        Test bulk sync handles invalid product ID formats gracefully.
        Requirements: 3.12, 3.13, 3.14
        """
        # Mock the export method for valid products
        mock_export.return_value = None
        
        product_ids = [self.products[0].id, 'invalid', self.products[1].id]
        
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': product_ids}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify the invalid ID is marked as error
        self.assertEqual(data['error_count'], 1)
        self.assertEqual(len(data['results']), 3)
        
        # Check the middle result (invalid ID)
        self.assertEqual(data['results'][1]['id'], 'invalid')
        self.assertFalse(data['results'][1]['success'])
        self.assertEqual(data['results'][1]['error'], 'Invalid product ID format')
    
    @patch('shopify_models.models.Product.export_to_shopify')
    def test_bulk_sync_result_count_matches_input(self, mock_export):
        """
        Test that bulk sync returns exactly N results for N product IDs.
        Requirements: 3.13, 3.14
        
        This validates Property 8: Bulk Operation Completeness
        """
        mock_export.return_value = None
        
        product_ids = [p.id for p in self.products]
        
        response = self.client.post(
            self.url,
            data=json.dumps({'product_ids': product_ids}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify exactly N results for N inputs
        self.assertEqual(len(data['results']), len(product_ids))
        
        # Verify each input ID has a corresponding result
        result_ids = [r['id'] for r in data['results']]
        self.assertEqual(result_ids, product_ids)
    
    def test_bulk_sync_only_accepts_post(self):
        """
        Test that bulk sync endpoint only accepts POST requests.
        """
        # GET should not be allowed
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # PUT should not be allowed
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 405)
        
        # DELETE should not be allowed
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 405)

