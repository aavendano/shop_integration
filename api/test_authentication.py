"""
Property-based tests for authentication and error handling.

These tests verify that the API layer properly handles authentication
and returns structured error responses.

Feature: shopify-polaris-ui-migration, Property 4: Structured Error Responses
"""
from django.test import TestCase, Client, override_settings
from accounts.models import Shop
from hypothesis import given, strategies as st, settings as hypothesis_settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
import jwt
import time
import json


@override_settings(
    SHOPIFY_CLIENT_ID='test_client_id',
    SHOPIFY_CLIENT_SECRET='test_client_secret'
)
class StructuredErrorResponsePropertyTest(HypothesisTestCase):
    """
    Property-based tests for structured error responses.
    
    Feature: shopify-polaris-ui-migration, Property 4: Structured Error Responses
    Validates: Requirements 1.7, 14.7
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create a test shop for authentication scenarios
        self.shop, _ = Shop.objects.get_or_create(
            myshopify_domain='test-shop.myshopify.com',
            defaults={
                'domain': 'test-shop.com',
                'name': 'Test Shop',
                'currency': 'USD',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'is_authentified': True
            }
        )
    
    def test_error_response_structure_for_missing_token(self):
        """
        Property 4: Structured Error Responses
        
        For any API error condition, the response should include an HTTP status code
        and a structured error message with detail field.
        
        Validates: Requirements 1.7, 14.7
        """
        endpoint = '/api/admin/context/'
        
        # Make request without Authorization header
        response = self.client.get(endpoint)
        
        # Should return 401 for missing token
        self.assertEqual(
            response.status_code,
            401,
            f"Expected 401 for missing token, got {response.status_code}"
        )
        
        # Should return JSON response
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Error response should be JSON"
        )
        
        # Parse response
        data = response.json()
        
        # Should have structured error response
        self.assertIsInstance(
            data,
            dict,
            "Error response should be a dictionary"
        )
        
        # Should contain detail field
        self.assertIn(
            'detail',
            data,
            "Error response should contain 'detail' field"
        )
        
        # Detail should be a string
        self.assertIsInstance(
            data['detail'],
            str,
            "'detail' field should be a string"
        )
        
        # Detail should not be empty
        self.assertTrue(
            len(data['detail']) > 0,
            "'detail' field should not be empty"
        )
    
    def test_error_response_structure_for_invalid_token(self):
        """
        Property 4: Structured Error Responses (Invalid token)
        
        For any API error condition with an invalid token,
        the response should include HTTP 401 and structured error message.
        
        Validates: Requirements 1.7, 14.7
        """
        endpoint = '/api/admin/context/'
        invalid_token = 'invalid.token.here'
        
        # Make request with invalid token
        response = self.client.get(
            endpoint,
            HTTP_AUTHORIZATION=f'Bearer {invalid_token}'
        )
        
        # Should return 401 for invalid token
        self.assertEqual(
            response.status_code,
            401,
            f"Expected 401 for invalid token, got {response.status_code}"
        )
        
        # Should return JSON response
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Error response should be JSON"
        )
        
        # Parse response
        data = response.json()
        
        # Should have structured error response
        self.assertIsInstance(
            data,
            dict,
            "Error response should be a dictionary"
        )
        
        # Should contain detail field
        self.assertIn(
            'detail',
            data,
            "Error response should contain 'detail' field"
        )
        
        # Should contain error_code field
        self.assertIn(
            'error_code',
            data,
            "Error response should contain 'error_code' field"
        )
        
        # error_code should be a string
        self.assertIsInstance(
            data['error_code'],
            str,
            "'error_code' field should be a string"
        )
        
        # error_code should indicate invalid token
        self.assertEqual(
            data['error_code'],
            'INVALID_TOKEN',
            f"Expected error_code 'INVALID_TOKEN', got {data['error_code']}"
        )
    
    def test_error_response_structure_for_expired_token(self):
        """
        Property 4: Structured Error Responses (Expired token)
        
        For any API error condition with an expired token,
        the response should include HTTP 401 and structured error message.
        
        Validates: Requirements 1.7, 14.7
        """
        # Create an expired JWT token
        current_time = int(time.time())
        payload = {
            'dest': f'https://{self.shop.myshopify_domain}',
            'aud': 'test_client_id',
            'iat': current_time - 7200,  # Issued 2 hours ago
            'exp': current_time - 3600,  # Expired 1 hour ago
        }
        
        token = jwt.encode(
            payload,
            'test_client_secret',
            algorithm='HS256'
        )
        
        endpoint = '/api/admin/context/'
        
        # Make request with expired token
        response = self.client.get(
            endpoint,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should return 401 for expired token
        self.assertEqual(
            response.status_code,
            401,
            f"Expected 401 for expired token, got {response.status_code}"
        )
        
        # Should return JSON response
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Error response should be JSON"
        )
        
        # Parse response
        data = response.json()
        
        # Should have structured error response
        self.assertIsInstance(
            data,
            dict,
            "Error response should be a dictionary"
        )
        
        # Should contain detail field
        self.assertIn(
            'detail',
            data,
            "Error response should contain 'detail' field"
        )
        
        # Should contain error_code field
        self.assertIn(
            'error_code',
            data,
            "Error response should contain 'error_code' field"
        )
        
        # error_code should indicate token expiration
        self.assertEqual(
            data['error_code'],
            'TOKEN_EXPIRED',
            f"Expected error_code 'TOKEN_EXPIRED', got {data['error_code']}"
        )
    
    def test_error_response_structure_for_nonexistent_shop(self):
        """
        Property 4: Structured Error Responses (Non-existent shop)
        
        For any API error condition with a valid token for a non-existent shop,
        the response should include HTTP 404 and structured error message.
        
        Validates: Requirements 1.7, 14.7
        """
        # Create a valid JWT token for a non-existent shop
        payload = {
            'dest': 'https://nonexistent-shop.myshopify.com',
            'aud': 'test_client_id',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }
        
        token = jwt.encode(
            payload,
            'test_client_secret',
            algorithm='HS256'
        )
        
        endpoint = '/api/admin/context/'
        
        # Make request with token for non-existent shop
        response = self.client.get(
            endpoint,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should return 404 for non-existent shop
        self.assertEqual(
            response.status_code,
            404,
            f"Expected 404 for non-existent shop, got {response.status_code}"
        )
        
        # Should return JSON response
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Error response should be JSON"
        )
        
        # Parse response
        data = response.json()
        
        # Should have structured error response
        self.assertIsInstance(
            data,
            dict,
            "Error response should be a dictionary"
        )
        
        # Should contain detail field
        self.assertIn(
            'detail',
            data,
            "Error response should contain 'detail' field"
        )
        
        # Should contain error_code field
        self.assertIn(
            'error_code',
            data,
            "Error response should contain 'error_code' field"
        )
        
        # error_code should indicate shop not found
        self.assertEqual(
            data['error_code'],
            'SHOP_NOT_FOUND',
            f"Expected error_code 'SHOP_NOT_FOUND', got {data['error_code']}"
        )
    
    @given(
        invalid_token=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
            min_size=10,
            max_size=50
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_all_error_responses_have_required_fields(self, invalid_token):
        """
        Property 4: Structured Error Responses (Hypothesis-based)
        
        For any API error response, the response should always include
        'detail' and 'error_code' fields.
        
        Validates: Requirements 1.7, 14.7
        """
        endpoint = '/api/admin/context/'
        
        # Make request with invalid token
        response = self.client.get(
            endpoint,
            HTTP_AUTHORIZATION=f'Bearer {invalid_token}'
        )
        
        # Should return error status code
        self.assertGreaterEqual(
            response.status_code,
            400,
            "Error response should have status code >= 400"
        )
        
        # Should return JSON response
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Error response should be JSON"
        )
        
        # Parse response
        data = response.json()
        
        # Should have structured error response
        self.assertIsInstance(
            data,
            dict,
            "Error response should be a dictionary"
        )
        
        # Should contain detail field
        self.assertIn(
            'detail',
            data,
            "Error response must contain 'detail' field"
        )
        
        # Detail should be a non-empty string
        self.assertIsInstance(
            data['detail'],
            str,
            "'detail' field should be a string"
        )
        
        self.assertTrue(
            len(data['detail']) > 0,
            "'detail' field should not be empty"
        )
        
        # Should contain error_code field
        self.assertIn(
            'error_code',
            data,
            "Error response must contain 'error_code' field"
        )
        
        # error_code should be a non-empty string
        self.assertIsInstance(
            data['error_code'],
            str,
            "'error_code' field should be a string"
        )
        
        self.assertTrue(
            len(data['error_code']) > 0,
            "'error_code' field should not be empty"
        )
    
    def test_error_response_consistency_across_endpoints(self):
        """
        Property 4: Structured Error Responses (Consistency)
        
        For any API endpoint, error responses should have consistent structure
        across all endpoints.
        
        Validates: Requirements 1.7, 14.7
        """
        endpoints = [
            '/api/admin/context/',
            '/api/admin/products/',
            '/api/admin/inventory/',
            '/api/admin/jobs/',
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                # Make request without token
                response = self.client.get(endpoint)
                
                # Should return error status code
                self.assertGreaterEqual(
                    response.status_code,
                    400,
                    f"Endpoint {endpoint} should return error status code"
                )
                
                # Should return JSON response
                self.assertEqual(
                    response['Content-Type'],
                    'application/json',
                    f"Endpoint {endpoint} should return JSON error response"
                )
                
                # Parse response
                data = response.json()
                
                # Should have consistent structure
                self.assertIn(
                    'detail',
                    data,
                    f"Endpoint {endpoint} error response should contain 'detail' field"
                )
                
                self.assertIsInstance(
                    data['detail'],
                    str,
                    f"Endpoint {endpoint} 'detail' field should be a string"
                )
