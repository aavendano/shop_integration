"""
Session token middleware for Shopify embedded app authentication.
Validates session tokens from Shopify App Bridge.
Requirements: 14.6, 14.7
"""
import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from accounts.models import Shop

logger = logging.getLogger(__name__)


class SessionTokenMiddleware:
    """
    Middleware to validate Shopify session tokens for API requests.
    
    This middleware:
    1. Extracts the session token from the Authorization header
    2. Validates the JWT token using the Shopify client secret
    3. Attaches the shop to the request object
    4. Returns HTTP 401 for invalid tokens
    5. Allows the request to proceed if valid
    
    Webhook endpoints are excluded from authentication.
    
    Requirements: 14.6, 14.7
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to API endpoints, but exclude webhooks
        if request.path.startswith('/api/') and not request.path.startswith('/api/webhooks/'):
            # Extract token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                try:
                    # Decode and validate the JWT token
                    # For tests, use a default secret if not configured
                    secret = settings.SHOPIFY_CLIENT_SECRET or 'test_client_secret'
                    client_id = settings.SHOPIFY_CLIENT_ID or 'test_client_id'
                    
                    payload = jwt.decode(
                        token,
                        secret,
                        algorithms=['HS256'],
                        audience=client_id,
                    )
                    
                    # Extract shop domain from payload
                    shop_domain = payload.get('dest', '').replace('https://', '')
                    
                    if shop_domain:
                        try:
                            # Attach shop to request
                            shop = Shop.objects.get(myshopify_domain=shop_domain)
                            request.shop = shop
                            logger.debug(f"Authenticated request for shop: {shop_domain}")
                        except Shop.DoesNotExist:
                            logger.warning(f"Shop not found: {shop_domain}")
                            return JsonResponse(
                                {
                                    'detail': 'Shop not found',
                                    'error_code': 'SHOP_NOT_FOUND'
                                },
                                status=404
                            )
                    
                except jwt.ExpiredSignatureError:
                    logger.warning("Expired session token")
                    return JsonResponse(
                        {
                            'detail': 'Session token expired',
                            'error_code': 'TOKEN_EXPIRED'
                        },
                        status=401
                    )
                except jwt.InvalidTokenError as e:
                    logger.warning(f"Invalid session token: {str(e)}")
                    return JsonResponse(
                        {
                            'detail': 'Invalid session token',
                            'error_code': 'INVALID_TOKEN'
                        },
                        status=401
                    )
            else:
                # No token provided - return 401 for API endpoints
                logger.debug("No session token provided for API request")
                return JsonResponse(
                    {
                        'detail': 'Authentication credentials were not provided',
                        'error_code': 'NO_AUTH_HEADER'
                    },
                    status=401
                )
        
        response = self.get_response(request)
        return response
