"""
Prices App Views

Views for managing Shopify contextual pricing including catalog/price list setup
and price synchronization.
"""

import logging
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from shopify_models.models import Product

logger = logging.getLogger(__name__)


class PricingSetupView(View):
    """View for setting up Catalog and Price List"""
    template_name = 'prices/setup.html'
    
    def get(self, request):
        from accounts.models import Session
        from django.conf import settings
        
        # Get session
        session = Session.objects.first()
        
        context = {
            'country': settings.SHOPIFY_COUNTRY,
            'provider_code': settings.SHOPIFY_PROVIDER_CODE,
            'catalog_name': settings.SHOPIFY_CATALOG_NAME,
            'currency': settings.SHOPIFY_CURRENCY,
            'catalog_id': settings.SHOPIFY_CATALOG_ID,
            'price_list_id': settings.SHOPIFY_PRICE_LIST_ID,
            'is_configured': bool(settings.SHOPIFY_CATALOG_ID and settings.SHOPIFY_PRICE_LIST_ID),
            'has_session': bool(session),
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        from accounts.models import Session
        from .services import get_or_create_catalog_and_price_list
        
        # Get session
        session = Session.objects.first()
        if not session:
            messages.error(request, "No active Shopify session found. Please authenticate first.")
            return redirect('prices:setup')
        
        # Create catalog and price list
        catalog_id, price_list_id, created = get_or_create_catalog_and_price_list(session)
        
        if catalog_id and price_list_id:
            if created:
                messages.success(
                    request,
                    f"Successfully created Catalog and Price List!<br>"
                    f"Catalog ID: {catalog_id}<br>"
                    f"Price List ID: {price_list_id}<br><br>"
                    f"Please add these to your .env file:",
                    extra_tags='safe'
                )
                messages.info(
                    request,
                    f"CATALOG_ID='{catalog_id}'<br>PRICE_LIST_ID='{price_list_id}'",
                    extra_tags='safe code'
                )
            else:
                messages.info(request, "Using existing Catalog and Price List from settings.")
        else:
            messages.error(request, "Failed to create Catalog and/or Price List. Check logs for details.")
        
        return redirect('prices:setup')


class ProductSyncPricesView(View):
    """View for syncing prices for a single product"""
    
    def post(self, request, pk):
        from accounts.models import Session
        from .services import sync_product_prices
        from django.conf import settings
        
        # Get product
        product = get_object_or_404(Product, pk=pk)
        
        # Check if price list is configured
        if not settings.SHOPIFY_PRICE_LIST_ID:
            messages.error(
                request,
                "Price List not configured. Please set up contextual pricing first."
            )
            return redirect('prices:setup')
        
        # Get session
        session = Session.objects.first()
        if not session:
            messages.error(request, "No active Shopify session found.")
            return redirect('shopify_models:product_detail', pk=pk)
        
        # Sync prices
        result = sync_product_prices(
            session=session,
            price_list_id=settings.SHOPIFY_PRICE_LIST_ID,
            product=product
        )
        
        # Show results
        if result['success_count'] > 0:
            messages.success(
                request,
                f"Successfully synced {result['success_count']} variant price(s) to Shopify."
            )
        
        if result['error_count'] > 0:
            error_msg = f"Failed to sync {result['error_count']} variant(s)."
            if result['errors']:
                error_msg += "<br>" + "<br>".join(result['errors'][:5])  # Show first 5 errors
            messages.error(request, error_msg, extra_tags='safe')
        
        if result['success_count'] == 0 and result['error_count'] == 0:
            messages.warning(request, result['errors'][0] if result['errors'] else "No variants to sync.")
        
        return redirect('shopify_models:product_detail', pk=pk)


class BulkSyncPricesView(View):
    """View for bulk syncing prices for multiple products"""
    
    def post(self, request):
        from accounts.models import Session
        from .services import sync_product_prices
        from django.conf import settings
        
        # Get selected product IDs
        product_ids = request.POST.getlist('product_ids')
        
        if not product_ids:
            messages.warning(request, "No products selected.")
            return redirect('shopify_models:product_list')
        
        # Check if price list is configured
        if not settings.SHOPIFY_PRICE_LIST_ID:
            messages.error(
                request,
                "Price List not configured. Please set up contextual pricing first."
            )
            return redirect('prices:setup')
        
        # Get session
        session = Session.objects.first()
        if not session:
            messages.error(request, "No active Shopify session found.")
            return redirect('shopify_models:product_list')
        
        # Sync prices for each product
        total_success = 0
        total_errors = 0
        
        for product_id in product_ids:
            try:
                product = Product.objects.get(pk=product_id)
                result = sync_product_prices(
                    session=session,
                    price_list_id=settings.SHOPIFY_PRICE_LIST_ID,
                    product=product
                )
                total_success += result['success_count']
                total_errors += result['error_count']
            except Product.DoesNotExist:
                logger.warning(f"Product {product_id} not found")
                continue
        
        # Show results
        if total_success > 0:
            messages.success(
                request,
                f"Successfully synced {total_success} variant price(s) from {len(product_ids)} product(s)."
            )
        
        if total_errors > 0:
            messages.error(
                request,
                f"Failed to sync {total_errors} variant(s). Check logs for details."
            )
        
        return redirect('shopify_models:product_list')
