"""
Test utilities for API tests.

Provides helper functions for creating JWT tokens and authenticated requests.
"""
import jwt
import time
from django.conf import settings
from accounts.models import Shop, Session


def create_jwt_token(shop_domain, client_id=None, client_secret=None, exp_offset=3600):
    """
    Create a valid JWT token for testing.
    
    Args:
        shop_domain: The shop's myshopify domain (e.g., 'test-shop.myshopify.com')
        client_id: Shopify client ID (defaults to settings.SHOPIFY_CLIENT_ID)
        client_secret: Shopify client secret (defaults to settings.SHOPIFY_CLIENT_SECRET)
        exp_offset: Token expiration offset in seconds (default 3600 = 1 hour)
    
    Returns:
        A valid JWT token string
    """
    if not client_id:
        client_id = getattr(settings, 'SHOPIFY_CLIENT_ID', None) or 'test_client_id'
    if not client_secret:
        client_secret = getattr(settings, 'SHOPIFY_CLIENT_SECRET', None) or 'test_client_secret'
    
    # Ensure both are strings
    client_id = str(client_id) if client_id else 'test_client_id'
    client_secret = str(client_secret) if client_secret else 'test_client_secret'
    
    payload = {
        'dest': f'https://{shop_domain}',
        'aud': client_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + exp_offset,
    }
    
    token = jwt.encode(
        payload,
        client_secret,
        algorithm='HS256'
    )
    
    # Ensure token is a string (jwt.encode returns string in newer versions)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return token


def create_expired_jwt_token(shop_domain, client_id=None, client_secret=None):
    """
    Create an expired JWT token for testing.
    
    Args:
        shop_domain: The shop's myshopify domain
        client_id: Shopify client ID
        client_secret: Shopify client secret
    
    Returns:
        An expired JWT token string
    """
    return create_jwt_token(shop_domain, client_id, client_secret, exp_offset=-3600)


def create_test_shop(myshopify_domain='test-shop.myshopify.com', **kwargs):
    """
    Create a test shop with default values.
    
    Args:
        myshopify_domain: The shop's myshopify domain
        **kwargs: Additional fields to set on the shop
    
    Returns:
        A Shop instance
    """
    defaults = {
        'domain': kwargs.get('domain', 'test-shop.com'),
        'name': kwargs.get('name', 'Test Shop'),
        'currency': kwargs.get('currency', 'USD'),
        'client_id': kwargs.get('client_id', 'test_client_id'),
        'client_secret': kwargs.get('client_secret', 'test_client_secret'),
        'is_authentified': kwargs.get('is_authentified', True),
    }
    
    # Remove any kwargs that are already in defaults
    for key in list(kwargs.keys()):
        if key in defaults:
            del kwargs[key]
    
    # Merge defaults with remaining kwargs
    defaults.update(kwargs)
    
    shop, created = Shop.objects.get_or_create(
        myshopify_domain=myshopify_domain,
        defaults=defaults
    )
    
    return shop


def create_test_session(shop=None, token='test_token', **kwargs):
    """
    Create a test session with default values.
    
    Args:
        shop: The shop for this session (creates one if not provided)
        token: The session token
        **kwargs: Additional fields to set on the session
    
    Returns:
        A Session instance
    """
    if shop is None:
        shop = create_test_shop()
    
    defaults = {
        'token': token,
        'site': kwargs.get('site', f'https://{shop.myshopify_domain}'),
    }
    
    # Remove any kwargs that are already in defaults
    for key in list(kwargs.keys()):
        if key in defaults:
            del kwargs[key]
    
    # Merge defaults with remaining kwargs
    defaults.update(kwargs)
    
    session, created = Session.objects.get_or_create(
        shop=shop,
        defaults=defaults
    )
    
    return session
