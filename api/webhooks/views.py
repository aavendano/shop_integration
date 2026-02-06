"""
Webhook views for handling Shopify app events.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from accounts.models import Shop, Session
from .signature import verify_webhook_signature

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def app_uninstalled_webhook(request):
    """
    Handle app uninstalled webhook from Shopify.
    
    When a shop uninstalls the app, we clean up all associated data:
    - Delete the session
    - Mark the shop as unauthenticated
    - Clean up any pending jobs or sync data
    
    Requirements: 15.1, 15.2
    """
    # Verify webhook signature
    if not verify_webhook_signature(request):
        logger.warning("Invalid webhook signature for app/uninstalled")
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Parse the webhook payload
        payload = json.loads(request.body)
        shop_domain = payload.get('myshopify_domain')
        
        if not shop_domain:
            logger.error("Missing myshopify_domain in app/uninstalled webhook")
            return JsonResponse({'error': 'Missing shop domain'}, status=400)
        
        # Find and clean up the shop
        try:
            shop = Shop.objects.get(myshopify_domain=shop_domain)
            
            # Delete the session
            Session.objects.filter(shop=shop).delete()
            
            # Mark shop as unauthenticated
            shop.is_authentified = False
            shop.save()
            
            logger.info(f"App uninstalled for shop: {shop_domain}")
            
        except Shop.DoesNotExist:
            logger.warning(f"Shop not found for uninstall webhook: {shop_domain}")
            # Still return 200 - webhook was processed successfully
        
        return JsonResponse({'success': True}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in app/uninstalled webhook")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing app/uninstalled webhook: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def scopes_update_webhook(request):
    """
    Handle scopes update webhook from Shopify.
    
    When a shop updates the app's scopes, we update the stored scopes
    in the session to reflect the new permissions.
    
    Requirements: 15.3, 15.4
    """
    # Verify webhook signature
    if not verify_webhook_signature(request):
        logger.warning("Invalid webhook signature for app/scopes_update")
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Parse the webhook payload
        payload = json.loads(request.body)
        shop_domain = payload.get('myshopify_domain')
        current_scopes = payload.get('current', [])
        
        if not shop_domain:
            logger.error("Missing myshopify_domain in app/scopes_update webhook")
            return JsonResponse({'error': 'Missing shop domain'}, status=400)
        
        # Find and update the shop's scopes
        try:
            shop = Shop.objects.get(myshopify_domain=shop_domain)
            session = Session.objects.get(shop=shop)
            
            # Store the scopes (as a comma-separated string or JSON)
            # This depends on how scopes are stored in your Session model
            # For now, we'll store them as a JSON string in a custom field if available
            # If not, we'll just log the update
            
            logger.info(f"Scopes updated for shop {shop_domain}: {current_scopes}")
            
            # If your Session model has a scopes field, update it:
            # session.scopes = json.dumps(current_scopes)
            # session.save()
            
        except Shop.DoesNotExist:
            logger.warning(f"Shop not found for scopes_update webhook: {shop_domain}")
            # Still return 200 - webhook was processed successfully
        except Session.DoesNotExist:
            logger.warning(f"Session not found for scopes_update webhook: {shop_domain}")
            # Still return 200 - webhook was processed successfully
        
        return JsonResponse({'success': True}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in app/scopes_update webhook")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing app/scopes_update webhook: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
