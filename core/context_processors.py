from django.conf import settings

def shopify_context(request):
    return {
        'SHOPIFY_API_KEY': settings.SHOPIFY_CLIENT_ID
    }
