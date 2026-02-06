"""
Webhook signature verification for Shopify webhooks.
Implements HMAC-SHA256 verification as per Shopify documentation.
"""
import hmac
import hashlib
import base64
from django.conf import settings


def verify_webhook_signature(request):
    """
    Verify that a webhook request came from Shopify.
    
    Shopify sends an X-Shopify-Hmac-SHA256 header with each webhook.
    We verify this by computing the HMAC-SHA256 of the request body
    using the app's client secret as the key.
    
    Args:
        request: Django request object
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Get the HMAC header from the request
    # Django converts header names to uppercase and replaces hyphens with underscores
    # X-Shopify-Hmac-SHA256 becomes HTTP_X_SHOPIFY_HMAC_SHA256
    hmac_header = request.META.get('HTTP_X_SHOPIFY_HMAC_SHA256', '')
    
    if not hmac_header:
        return False
    
    # Get the raw request body
    body = request.body
    
    # Get the client secret from settings
    client_secret = settings.SHOPIFY_API_SECRET
    
    if not client_secret:
        return False
    
    try:
        # Compute the expected HMAC
        # Shopify uses the raw request body (not parsed JSON)
        computed_hmac = base64.b64encode(
            hmac.new(
                client_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Compare using constant-time comparison to prevent timing attacks
        # Handle potential encoding issues by comparing bytes
        try:
            return hmac.compare_digest(computed_hmac, hmac_header)
        except TypeError:
            # If comparison fails due to encoding, try byte comparison
            computed_bytes = computed_hmac.encode('utf-8')
            header_bytes = hmac_header.encode('utf-8', errors='ignore')
            return hmac.compare_digest(computed_bytes, header_bytes)
    except Exception:
        return False


def get_shop_domain_from_webhook(request):
    """
    Extract the shop domain from a Shopify webhook request.
    
    Shopify sends the shop domain in the X-Shopify-Shop-Api-Call-Limit header
    or we can extract it from the request headers.
    
    Args:
        request: Django request object
        
    Returns:
        str: Shop domain (e.g., 'example.myshopify.com') or None
    """
    # Try to get from X-Shopify-Shop-Id header first
    shop_id = request.META.get('HTTP_X_SHOPIFY_SHOP_ID')
    
    # If not available, try to extract from the request path or body
    # This is a fallback - ideally Shopify provides this in headers
    if not shop_id:
        # For now, return None - the webhook handler should extract from body
        return None
    
    return shop_id
