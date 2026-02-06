"""
Tests for the API app.
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Shop, User
from api.models import Job, JobLog
from api.test_utils import create_jwt_token, create_test_shop, create_test_session
from django.utils import timezone
from datetime import timedelta
import json


class ContextViewTestCase(TestCase):
    """Test the context API endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/context/'
        
        # Create a test shop
        self.shop = create_test_shop()
        
        # Create a test session
        self.session = create_test_session(shop=self.shop)
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create JWT token for authenticated requests
        self.token = create_jwt_token(self.shop.myshopify_domain)
    
    def test_successful_context_retrieval(self):
        """
        Test successful context retrieval with valid session.
        Requirements: 2.1, 2.2
        """
        # Make authenticated request with JWT token
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('shop', data)
        self.assertIn('user', data)
        self.assertIn('config', data)
        self.assertIn('permissions', data)
    
    def test_missing_session_returns_401(self):
        """
        Test that missing authentication returns 401.
        Requirements: 2.5
        """
        # Make request without authentication
        response = self.client.get(self.url)
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertIn('detail', data)
    
    def test_response_structure(self):
        """
        Test that response has correct structure.
        Requirements: 2.2, 2.3, 2.4
        """
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Verify shop structure
        self.assertIn('shop', data)
        self.assertIn('domain', data['shop'])
        self.assertIn('name', data['shop'])
        self.assertIn('currency', data['shop'])
        self.assertIn('is_authenticated', data['shop'])
        
        # Verify user structure
        self.assertIn('user', data)
        self.assertIn('username', data['user'])
        self.assertIn('is_authenticated', data['user'])
        self.assertIn('is_staff', data['user'])
        
        # Verify config structure
        self.assertIn('config', data)
        self.assertIn('api_version', data['config'])
        self.assertIn('country', data['config'])
        self.assertIn('provider_code', data['config'])
        self.assertIn('catalog_name', data['config'])
        
        # Verify permissions structure
        self.assertIn('permissions', data)
        self.assertIn('can_sync_products', data['permissions'])
        self.assertIn('can_manage_inventory', data['permissions'])
        self.assertIn('can_view_orders', data['permissions'])
        
        # Verify permission values are boolean
        self.assertIsInstance(data['permissions']['can_sync_products'], bool)
        self.assertIsInstance(data['permissions']['can_manage_inventory'], bool)
        self.assertIsInstance(data['permissions']['can_view_orders'], bool)


class SessionTokenMiddlewareTestCase(TestCase):
    """Test the session token middleware."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/context/'
        
        # Create a test shop and token
        self.shop = create_test_shop()
        self.token = create_jwt_token(self.shop.myshopify_domain)
    
    def test_request_without_token_returns_401(self):
        """Test that requests without token return 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
    
    def test_request_with_valid_token_succeeds(self):
        """Test that requests with valid token succeed."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_request_with_invalid_token_returns_401(self):
        """Test that requests with invalid token return 401."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        self.assertEqual(response.status_code, 401)


class JobListViewTestCase(TestCase):
    """Test the jobs list API endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/jobs/'
        
        # Create test shop and JWT token
        self.shop = create_test_shop()
        self.token = create_jwt_token(self.shop.myshopify_domain)
        
        # Create test jobs with various statuses and types
        self.job1 = Job.objects.create(
            job_type='product_sync',
            status='completed',
            progress=100,
            started_at=timezone.now() - timedelta(hours=2),
            completed_at=timezone.now() - timedelta(hours=1)
        )
        
        self.job2 = Job.objects.create(
            job_type='bulk_sync',
            status='running',
            progress=50,
            started_at=timezone.now() - timedelta(minutes=30)
        )
        
        self.job3 = Job.objects.create(
            job_type='inventory_reconcile',
            status='pending',
            progress=0
        )
        
        self.job4 = Job.objects.create(
            job_type='product_sync',
            status='failed',
            progress=25,
            started_at=timezone.now() - timedelta(hours=3),
            completed_at=timezone.now() - timedelta(hours=3),
            error_message='Shopify API error'
        )
    
    def test_list_all_jobs(self):
        """
        Test listing all jobs without filters.
        Requirements: 6.1
        """
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        
        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 4)
    
    def test_filter_by_status(self):
        """
        Test filtering jobs by status.
        Requirements: 6.3
        """
        # Filter for running jobs
        response = self.client.get(
            self.url,
            {'status': 'running'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'running')
        self.assertEqual(data['results'][0]['job_type'], 'bulk_sync')
        
        # Filter for completed jobs
        response = self.client.get(
            self.url,
            {'status': 'completed'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'completed')
    
    def test_filter_by_job_type(self):
        """
        Test filtering jobs by job type.
        Requirements: 6.3
        """
        # Filter for product_sync jobs
        response = self.client.get(
            self.url,
            {'job_type': 'product_sync'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results are product_sync
        for job in data['results']:
            self.assertEqual(job['job_type'], 'product_sync')
        
        # Filter for inventory_reconcile jobs
        response = self.client.get(
            self.url,
            {'job_type': 'inventory_reconcile'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['job_type'], 'inventory_reconcile')
    
    def test_filter_by_status_and_job_type(self):
        """
        Test filtering jobs by both status and job type.
        Requirements: 6.3
        """
        response = self.client.get(self.url, {
            'status': 'failed',
            'job_type': 'product_sync'
        })
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'failed')
        self.assertEqual(data['results'][0]['job_type'], 'product_sync')
    
    def test_pagination_default_page_size(self):
        """
        Test pagination with default page size.
        Requirements: 6.1
        """
        # Create more jobs to test pagination
        for i in range(60):
            Job.objects.create(
                job_type='product_sync',
                status='pending',
                progress=0
            )
        
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 64)  # 4 original + 60 new
        self.assertEqual(len(data['results']), 50)  # Default page size
        self.assertIn('next', data)
        self.assertIsNotNone(data['next'])
    
    def test_pagination_custom_page_size(self):
        """
        Test pagination with custom page size.
        Requirements: 6.1
        """
        response = self.client.get(self.url, {'page_size': '2'})
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 2)
        self.assertIn('next', data)
        self.assertIsNotNone(data['next'])
    
    def test_pagination_second_page(self):
        """
        Test accessing second page of results.
        Requirements: 6.1
        """
        response = self.client.get(self.url, {'page': '2', 'page_size': '2'})
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 2)
        self.assertIn('previous', data)
        self.assertIsNotNone(data['previous'])
    
    def test_response_includes_required_fields(self):
        """
        Test that response includes all required fields.
        Requirements: 6.2
        """
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Check first job has all required fields
        job = data['results'][0]
        required_fields = [
            'id', 'job_type', 'status', 'progress',
            'started_at', 'completed_at', 'duration',
            'error_message', 'created_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, job, f"Missing required field: {field}")
    
    def test_jobs_ordered_by_created_at_desc(self):
        """
        Test that jobs are ordered by created_at descending (newest first).
        Requirements: 6.1
        """
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify jobs are in descending order by created_at
        results = data['results']
        for i in range(len(results) - 1):
            current_created = results[i]['created_at']
            next_created = results[i + 1]['created_at']
            self.assertGreaterEqual(current_created, next_created)


class ProductListViewTestCase(TestCase):
    """Test the products list API endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/products/'
        
        # Create test shop and JWT token
        self.shop = create_test_shop()
        self.token = create_jwt_token(self.shop.myshopify_domain)
        
        # Create test products with various attributes
        from shopify_models.models import Product, Variant, InventoryItem
        
        self.product1 = Product.objects.create(
            title='Test Product 1',
            vendor='Vendor A',
            product_type='Type A',
            tags='tag1, tag2',
            handle='test-product-1',
            shopify_id='gid://shopify/Product/123'
        )
        
        self.product2 = Product.objects.create(
            title='Test Product 2',
            vendor='Vendor B',
            product_type='Type B',
            tags='tag2, tag3',
            handle='test-product-2',
            shopify_id='gid://shopify/Product/456'
        )
        
        self.product3 = Product.objects.create(
            title='Another Product',
            vendor='Vendor A',
            product_type='Type A',
            tags='tag1',
            handle='another-product',
            shopify_id=None  # Not synced yet
        )
        
        self.product4 = Product.objects.create(
            title='Special Product',
            vendor='Vendor C',
            product_type='Type C',
            tags='special',
            handle='special-product',
            shopify_id='gid://shopify/Product/789'
        )
        
        # Create variants for products
        self.variant1 = Variant.objects.create(
            product=self.product1,
            title='Default',
            supplier_sku='SKU1',
            price='99.99',
            grams=100,  # Required field
            shopify_id='gid://shopify/ProductVariant/111'
        )
        
        self.variant2 = Variant.objects.create(
            product=self.product2,
            title='Default',
            supplier_sku='SKU2',
            price='149.99',
            grams=150,  # Required field
            shopify_id='gid://shopify/ProductVariant/222'
        )
    
    def test_list_all_products(self):
        """
        Test listing all products without filters.
        Requirements: 3.1
        """
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        
        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 4)
    
    def test_filter_by_title(self):
        """
        Test filtering products by title.
        Requirements: 3.3
        """
        # Filter for products with "Test" in title
        response = self.client.get(
            self.url,
            {'title': 'Test'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results contain "Test" in title
        for product in data['results']:
            self.assertIn('Test', product['title'])
        
        # Filter for specific product
        response = self.client.get(
            self.url,
            {'title': 'Special'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'Special Product')
    
    def test_filter_by_vendor(self):
        """
        Test filtering products by vendor.
        Requirements: 3.3
        """
        # Filter for Vendor A products
        response = self.client.get(
            self.url,
            {'vendor': 'Vendor A'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results have Vendor A
        for product in data['results']:
            self.assertEqual(product['vendor'], 'Vendor A')
        
        # Filter for Vendor C products
        response = self.client.get(
            self.url,
            {'vendor': 'Vendor C'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['vendor'], 'Vendor C')
    
    def test_filter_by_product_type(self):
        """
        Test filtering products by product type.
        Requirements: 3.3
        """
        # Filter for Type A products
        response = self.client.get(
            self.url,
            {'product_type': 'Type A'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results have Type A
        for product in data['results']:
            self.assertEqual(product['product_type'], 'Type A')
    
    def test_filter_by_tags(self):
        """
        Test filtering products by tags.
        Requirements: 3.3
        """
        # Filter for products with tag1
        response = self.client.get(
            self.url,
            {'tags': 'tag1'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results contain tag1
        for product in data['results']:
            self.assertIn('tag1', product['tags'])
        
        # Filter for products with special tag
        response = self.client.get(
            self.url,
            {'tags': 'special'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['tags'], 'special')
    
    def test_multiple_filters(self):
        """
        Test filtering products with multiple filters.
        Requirements: 3.3
        """
        response = self.client.get(
            self.url,
            {
                'vendor': 'Vendor A',
                'product_type': 'Type A'
            },
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Verify all results match both filters
        for product in data['results']:
            self.assertEqual(product['vendor'], 'Vendor A')
            self.assertEqual(product['product_type'], 'Type A')
    
    def test_sort_by_created_at_ascending(self):
        """
        Test sorting products by created_at ascending.
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': 'created_at'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify products are in ascending order by created_at
        results = data['results']
        for i in range(len(results) - 1):
            current_created = results[i]['created_at']
            next_created = results[i + 1]['created_at']
            self.assertLessEqual(current_created, next_created)
    
    def test_sort_by_created_at_descending(self):
        """
        Test sorting products by created_at descending (default).
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': '-created_at'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify products are in descending order by created_at
        results = data['results']
        for i in range(len(results) - 1):
            current_created = results[i]['created_at']
            next_created = results[i + 1]['created_at']
            self.assertGreaterEqual(current_created, next_created)
    
    def test_sort_by_title_ascending(self):
        """
        Test sorting products by title ascending.
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': 'title'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify products are in ascending order by title
        results = data['results']
        for i in range(len(results) - 1):
            current_title = results[i]['title']
            next_title = results[i + 1]['title']
            self.assertLessEqual(current_title, next_title)
    
    def test_sort_by_title_descending(self):
        """
        Test sorting products by title descending.
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': '-title'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify products are in descending order by title
        results = data['results']
        for i in range(len(results) - 1):
            current_title = results[i]['title']
            next_title = results[i + 1]['title']
            self.assertGreaterEqual(current_title, next_title)
    
    def test_sort_by_updated_at(self):
        """
        Test sorting products by updated_at.
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': 'updated_at'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify products are in ascending order by updated_at
        results = data['results']
        for i in range(len(results) - 1):
            current_updated = results[i]['last_synced_at']
            next_updated = results[i + 1]['last_synced_at']
            self.assertLessEqual(current_updated, next_updated)
    
    def test_pagination_default_page_size(self):
        """
        Test pagination with default page size of 50.
        Requirements: 3.2, 20.3
        """
        # Create more products to test pagination
        from shopify_models.models import Product
        for i in range(60):
            Product.objects.create(
                title=f'Product {i}',
                vendor='Test Vendor',
                product_type='Test Type',
                handle=f'product-{i}'
            )
        
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 64)  # 4 original + 60 new
        self.assertEqual(len(data['results']), 50)  # Default page size
        self.assertIn('next', data)
        self.assertIsNotNone(data['next'])
    
    def test_pagination_custom_page_size(self):
        """
        Test pagination with custom page size.
        Requirements: 3.2
        """
        response = self.client.get(
            self.url,
            {'page_size': '2'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 2)
        self.assertIn('next', data)
        self.assertIsNotNone(data['next'])
    
    def test_pagination_max_page_size(self):
        """
        Test pagination enforces maximum page size of 100.
        Requirements: 3.2
        """
        response = self.client.get(
            self.url,
            {'page_size': '200'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        # Should be limited to 100 even though we requested 200
        self.assertLessEqual(len(data['results']), 100)
    
    def test_pagination_second_page(self):
        """
        Test accessing second page of results.
        Requirements: 3.2
        """
        response = self.client.get(
            self.url,
            {'page': '2', 'page_size': '2'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 2)
        self.assertIn('previous', data)
        self.assertIsNotNone(data['previous'])
    
    def test_response_includes_required_fields(self):
        """
        Test that response includes all required fields.
        Requirements: 3.5
        """
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Check first product has all required fields
        product = data['results'][0]
        required_fields = [
            'id', 'title', 'vendor', 'product_type', 'tags',
            'variant_count', 'sync_status', 'last_synced_at', 'created_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, product, f"Missing required field: {field}")
    
    def test_variant_count_calculation(self):
        """
        Test that variant_count is correctly calculated.
        Requirements: 3.5
        """
        response = self.client.get(
            self.url,
            {'title': 'Test Product 1'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 1)
        
        product = data['results'][0]
        self.assertEqual(product['variant_count'], 1)
    
    def test_sync_status_pending_for_unsynced_product(self):
        """
        Test that sync_status is 'pending' for products without shopify_id.
        Requirements: 3.5
        """
        response = self.client.get(
            self.url,
            {'title': 'Another Product'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 1)
        
        product = data['results'][0]
        self.assertEqual(product['sync_status'], 'pending')
    
    def test_sync_status_synced_for_synced_product(self):
        """
        Test that sync_status is 'synced' for products with shopify_id.
        Requirements: 3.5
        """
        response = self.client.get(
            self.url,
            {'title': 'Test Product 1'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['results']), 1)
        
        product = data['results'][0]
        self.assertEqual(product['sync_status'], 'synced')
    
    def test_invalid_ordering_uses_default(self):
        """
        Test that invalid ordering parameter uses default ordering.
        Requirements: 3.4
        """
        response = self.client.get(
            self.url,
            {'ordering': 'invalid_field'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        
        # Should default to -created_at (descending)
        results = data['results']
        for i in range(len(results) - 1):
            current_created = results[i]['created_at']
            next_created = results[i + 1]['created_at']
            self.assertGreaterEqual(current_created, next_created)
    
    def test_case_insensitive_filtering(self):
        """
        Test that filters are case-insensitive.
        Requirements: 3.3
        """
        # Filter with lowercase
        response = self.client.get(
            self.url,
            {'vendor': 'vendor a'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
        
        # Filter with uppercase
        response = self.client.get(
            self.url,
            {'vendor': 'VENDOR A'},
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 2)
