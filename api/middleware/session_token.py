"""
Session token middleware for Shopify embedded app authentication.
Validates session tokens from Shopify App Bridge.
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
    4. Allows the request to proceed if valid
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to API endpoints
        if request.path.startswith('/api/'):
            # Extract token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                try:
                    # Decode and validate the JWT token
                    payload = jwt.decode(
                        token,
                        settings.SHOPIFY_CLIENT_SECRET,
                        algorithms=['HS256'],
                        audience=settings.SHOPIFY_CLIENT_ID,
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
                                {'error': 'Shop not found'},
                                status=404
                            )
                    
                except jwt.ExpiredSignatureError:
                    logger.warning("Expired session token")
                    return JsonResponse(
                        {'error': 'Session token expired'},
                        status=401
                    )
                except jwt.InvalidTokenError as e:
                    logger.warning(f"Invalid session token: {str(e)}")
                    return JsonResponse(
                        {'error': 'Invalid session token'},
                        status=401
                    )
            else:
                # No token provided - allow for development/testing
                # In production, you might want to return 401 here
                logger.debug("No session token provided")
                request.shop = None
        
        response = self.get_response(request)
        return response
