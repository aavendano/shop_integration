"""
Tests for the API app.
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Shop, User
import json


class ContextViewTestCase(TestCase):
    """Test the context API endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/context/'
    
    def test_context_endpoint_returns_200(self):
        """Test that the context endpoint returns a 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_context_endpoint_returns_json(self):
        """Test that the context endpoint returns JSON data."""
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('shop', data)
        self.assertIn('user', data)
        self.assertIn('config', data)
        self.assertIn('permissions', data)
    
    def test_context_includes_shop_info(self):
        """Test that context includes shop information."""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertIn('domain', data['shop'])
        self.assertIn('name', data['shop'])
        self.assertIn('currency', data['shop'])
        self.assertIn('is_authenticated', data['shop'])
    
    def test_context_includes_user_info(self):
        """Test that context includes user information."""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertIn('username', data['user'])
        self.assertIn('is_authenticated', data['user'])
        self.assertIn('is_staff', data['user'])
    
    def test_context_includes_config(self):
        """Test that context includes configuration."""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertIn('api_version', data['config'])
        self.assertIn('country', data['config'])
        self.assertIn('provider_code', data['config'])
        self.assertIn('catalog_name', data['config'])
    
    def test_context_includes_permissions(self):
        """Test that context includes permissions."""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertIn('can_sync_products', data['permissions'])
        self.assertIn('can_manage_inventory', data['permissions'])
        self.assertIn('can_view_orders', data['permissions'])


class SessionTokenMiddlewareTestCase(TestCase):
    """Test the session token middleware."""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/admin/context/'
    
    def test_request_without_token_succeeds(self):
        """Test that requests without token are allowed (for development)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_request_with_invalid_token_returns_401(self):
        """Test that requests with invalid token return 401."""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        self.assertEqual(response.status_code, 401)
