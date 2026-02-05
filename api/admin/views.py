"""
Admin API views for Shopify Polaris UI.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


class ContextView(APIView):
    """
    Returns context information for the Shopify Polaris UI.
    Includes shop details, user info, permissions, and UI flags.
    """
    
    def get(self, request):
        """
        GET /api/admin/context/
        Returns shop context, user info, and UI configuration.
        """
        # Get shop from session or request
        shop = getattr(request, 'shop', None)
        
        context_data = {
            'shop': {
                'domain': shop.myshopify_domain if shop else None,
                'name': shop.name if shop else None,
                'currency': shop.currency if shop else settings.SHOPIFY_CURRENCY,
                'is_authenticated': shop.is_authentified if shop else False,
            },
            'user': {
                'username': request.user.username if request.user.is_authenticated else None,
                'is_authenticated': request.user.is_authenticated,
                'is_staff': request.user.is_staff if request.user.is_authenticated else False,
            },
            'config': {
                'api_version': settings.API_VERSION,
                'country': settings.SHOPIFY_COUNTRY,
                'provider_code': settings.SHOPIFY_PROVIDER_CODE,
                'catalog_name': settings.SHOPIFY_CATALOG_NAME,
            },
            'permissions': {
                'can_sync_products': True,  # To be implemented based on actual permissions
                'can_manage_inventory': True,
                'can_view_orders': True,
            }
        }
        
        return Response(context_data, status=status.HTTP_200_OK)
