"""
Integration tests for the API infrastructure.
"""
from django.test import TestCase, Client, override_settings
from django.conf import settings
from accounts.models import Shop
import jwt
import time


@override_settings(
    SHOPIFY_CLIENT_ID='test_client_id',
    SHOPIFY_CLIENT_SECRET='test_client_secret'
)
class APIInfrastructureIntegrationTest(TestCase):
    """Integration tests for the complete API infrastructure."""
    
    def setUp(self):
        self.client = Client()
        
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
    
    def test_api_url_routing(self):
        """Test that API URLs are properly routed."""
        response = self.client.get('/api/admin/context/')
        self.assertEqual(response.status_code, 200)
    
    def test_context_endpoint_with_valid_token(self):
        """Test context endpoint with a valid session token."""
        # Create a valid JWT token
        payload = {
            'dest': f'https://{self.shop.myshopify_domain}',
            'aud': 'test_client_id',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }
        
        token = jwt.encode(
            payload,
            'test_client_secret',
            algorithm='HS256'
        )
        
        # Make request with token
        response = self.client.get(
            '/api/admin/context/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify shop information is included
        self.assertEqual(data['shop']['domain'], self.shop.myshopify_domain)
        self.assertEqual(data['shop']['name'], self.shop.name)
        self.assertEqual(data['shop']['currency'], self.shop.currency)
        self.assertTrue(data['shop']['is_authenticated'])
    
    def test_middleware_rejects_expired_token(self):
        """Test that middleware rejects expired tokens."""
        # Create an expired JWT token
        payload = {
            'dest': f'https://{self.shop.myshopify_domain}',
            'aud': 'test_client_id',
            'iat': int(time.time()) - 7200,
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
        }
        
        token = jwt.encode(
            payload,
            'test_client_secret',
            algorithm='HS256'
        )
        
        # Make request with expired token
        response = self.client.get(
            '/api/admin/context/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Session token expired')
    
    def test_middleware_rejects_invalid_signature(self):
        """Test that middleware rejects tokens with invalid signature."""
        # Create a token with wrong secret
        payload = {
            'dest': f'https://{self.shop.myshopify_domain}',
            'aud': 'test_client_id',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }
        
        token = jwt.encode(
            payload,
            'wrong_secret',
            algorithm='HS256'
        )
        
        # Make request with invalid token
        response = self.client.get(
            '/api/admin/context/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid session token')
    
    def test_rest_framework_configuration(self):
        """Test that Django REST Framework is properly configured."""
        self.assertIn('rest_framework', settings.INSTALLED_APPS)
        self.assertIsNotNone(settings.REST_FRAMEWORK)
        self.assertEqual(
            settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'],
            'rest_framework.pagination.PageNumberPagination'
        )
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 50)
