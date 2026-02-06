"""
Tests for webhook handling.

These tests verify that webhook endpoints properly handle Shopify app events,
verify signatures, and clean up data appropriately.

Feature: shopify-polaris-ui-migration, Property 15: Webhook Signature Verification
"""
import json
import hmac
import hashlib
import base64
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from accounts.models import Shop, Session
from hypothesis import given, strategies as st, settings as hypothesis_settings
from hypothesis.extra.django import TestCase as HypothesisTestCase


def create_webhook_signature(body, secret):
    """Helper to create valid webhook signatures."""
    return base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
    ).decode('utf-8')


@override_settings(
    SHOPIFY_CLIENT_ID='test_client_id',
    SHOPIFY_CLIENT_SECRET='test_client_secret',
    SHOPIFY_API_SECRET='test_api_secret'
)
class AppUninstalledWebhookTest(TestCase):
    """
    Tests for app uninstalled webhook endpoint.
    
    Requirements: 15.1, 15.2
    """
    
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('api:webhooks:app-uninstalled')
        
        # Create a test shop with session
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            domain='test-shop.com',
            name='Test Shop',
            currency='USD',
            client_id='test_client_id',
            client_secret='test_client_secret',
            is_authentified=True
        )
        
        self.session = Session.objects.create(
            shop=self.shop,
            token='test_token',
            site='https://test-shop.myshopify.com'
        )
    
    def test_app_uninstalled_with_valid_signature(self):
        """
        Test that app uninstalled webhook with valid signature cleans up shop data.
        
        Requirement 15.1: THE Remix_Frontend SHALL provide a webhook endpoint at `/webhooks/app/uninstalled`
        Requirement 15.2: WHEN app uninstalled webhook is received, THE Remix_Frontend SHALL clean up shop data
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify shop is marked as unauthenticated
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.is_authentified)
        
        # Verify session is deleted
        self.assertFalse(Session.objects.filter(shop=self.shop).exists())
    
    def test_app_uninstalled_with_invalid_signature(self):
        """
        Test that app uninstalled webhook with invalid signature returns 401.
        
        Requirement 15.5: THE Remix_Frontend SHALL verify webhook HMAC signatures
        Requirement 15.6: WHEN webhook signature is invalid, THE Remix_Frontend SHALL return HTTP 401
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        invalid_signature = 'invalid_signature_here'
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=invalid_signature
        )
        
        self.assertEqual(response.status_code, 401)
        
        # Verify shop data is NOT cleaned up
        self.shop.refresh_from_db()
        self.assertTrue(self.shop.is_authentified)
        self.assertTrue(Session.objects.filter(shop=self.shop).exists())
    
    def test_app_uninstalled_without_signature(self):
        """
        Test that app uninstalled webhook without signature returns 401.
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_app_uninstalled_with_missing_shop_domain(self):
        """
        Test that app uninstalled webhook with missing shop domain returns 400.
        """
        payload = {}
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_app_uninstalled_with_nonexistent_shop(self):
        """
        Test that app uninstalled webhook for nonexistent shop returns 200.
        
        Webhook should be idempotent - if shop doesn't exist, still return success.
        """
        payload = {
            'myshopify_domain': 'nonexistent-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_app_uninstalled_with_invalid_json(self):
        """
        Test that app uninstalled webhook with invalid JSON returns 400.
        """
        body = b'invalid json {'
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 400)


@override_settings(
    SHOPIFY_CLIENT_ID='test_client_id',
    SHOPIFY_CLIENT_SECRET='test_client_secret',
    SHOPIFY_API_SECRET='test_api_secret'
)
class ScopesUpdateWebhookTest(TestCase):
    """
    Tests for scopes update webhook endpoint.
    
    Requirements: 15.3, 15.4
    """
    
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('api:webhooks:app-scopes-update')
        
        # Create a test shop with session
        self.shop = Shop.objects.create(
            myshopify_domain='test-shop.myshopify.com',
            domain='test-shop.com',
            name='Test Shop',
            currency='USD',
            client_id='test_client_id',
            client_secret='test_client_secret',
            is_authentified=True
        )
        
        self.session = Session.objects.create(
            shop=self.shop,
            token='test_token',
            site='https://test-shop.myshopify.com'
        )
    
    def test_scopes_update_with_valid_signature(self):
        """
        Test that scopes update webhook with valid signature processes successfully.
        
        Requirement 15.3: THE Remix_Frontend SHALL provide a webhook endpoint at `/webhooks/app/scopes_update`
        Requirement 15.4: WHEN scopes update webhook is received, THE Remix_Frontend SHALL update stored scopes
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com',
            'current': ['read_products', 'write_products', 'read_orders']
        }
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify shop still exists and is authenticated
        self.shop.refresh_from_db()
        self.assertTrue(self.shop.is_authentified)
    
    def test_scopes_update_with_invalid_signature(self):
        """
        Test that scopes update webhook with invalid signature returns 401.
        
        Requirement 15.5: THE Remix_Frontend SHALL verify webhook HMAC signatures
        Requirement 15.6: WHEN webhook signature is invalid, THE Remix_Frontend SHALL return HTTP 401
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com',
            'current': ['read_products', 'write_products']
        }
        body = json.dumps(payload).encode('utf-8')
        invalid_signature = 'invalid_signature_here'
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=invalid_signature
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_scopes_update_without_signature(self):
        """
        Test that scopes update webhook without signature returns 401.
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com',
            'current': ['read_products']
        }
        body = json.dumps(payload).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_scopes_update_with_missing_shop_domain(self):
        """
        Test that scopes update webhook with missing shop domain returns 400.
        """
        payload = {
            'current': ['read_products']
        }
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_scopes_update_with_nonexistent_shop(self):
        """
        Test that scopes update webhook for nonexistent shop returns 200.
        
        Webhook should be idempotent - if shop doesn't exist, still return success.
        """
        payload = {
            'myshopify_domain': 'nonexistent-shop.myshopify.com',
            'current': ['read_products']
        }
        body = json.dumps(payload).encode('utf-8')
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_scopes_update_with_invalid_json(self):
        """
        Test that scopes update webhook with invalid JSON returns 400.
        """
        body = b'invalid json {'
        signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=signature
        )
        
        self.assertEqual(response.status_code, 400)


@override_settings(
    SHOPIFY_CLIENT_ID='test_client_id',
    SHOPIFY_CLIENT_SECRET='test_client_secret',
    SHOPIFY_API_SECRET='test_api_secret'
)
class WebhookSignatureVerificationPropertyTest(HypothesisTestCase):
    """
    Property-based tests for webhook signature verification.
    
    Feature: shopify-polaris-ui-migration, Property 15: Webhook Signature Verification
    Validates: Requirements 15.5, 15.6
    """
    
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('api:webhooks:app-uninstalled')
        
        # Create a test shop using get_or_create to avoid duplicates
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
        
        Session.objects.get_or_create(
            shop=self.shop,
            defaults={
                'token': 'test_token',
                'site': 'https://test-shop.myshopify.com'
            }
        )
    
    @given(st.text())
    @hypothesis_settings(max_examples=50)
    def test_invalid_signatures_always_rejected(self, invalid_sig):
        """
        Property 15: Webhook Signature Verification
        
        For any invalid signature, the webhook endpoint should return HTTP 401.
        
        Validates: Requirements 15.5, 15.6
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=invalid_sig
        )
        
        # Invalid signatures should always be rejected
        self.assertEqual(response.status_code, 401)
    
    def test_valid_signature_always_accepted(self):
        """
        Property 15: Webhook Signature Verification
        
        For any valid signature, the webhook endpoint should return HTTP 200.
        
        Validates: Requirements 15.5, 15.6
        """
        payload = {
            'myshopify_domain': 'test-shop.myshopify.com'
        }
        body = json.dumps(payload).encode('utf-8')
        valid_signature = create_webhook_signature(body, 'test_api_secret')
        
        response = self.client.post(
            self.webhook_url,
            data=body,
            content_type='application/json',
            HTTP_X_SHOPIFY_HMAC_SHA256=valid_signature
        )
        
        # Valid signatures should always be accepted
        self.assertEqual(response.status_code, 200)
