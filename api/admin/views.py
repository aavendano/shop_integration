"""
Admin API views for Shopify Polaris UI.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.db.models import Q
from api.models import Job
from api.serializers.jobs import JobListSerializer
from api.serializers.products import ProductListSerializer, ProductDetailSerializer
from api.serializers.inventory import InventoryItemSerializer
from shopify_models.models import Product, InventoryItem


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


class JobListView(APIView):
    """
    Returns paginated list of background jobs with filtering support.
    
    Supports filtering by:
    - status: Filter by job status (pending, running, completed, failed)
    - job_type: Filter by job type (product_sync, bulk_sync, etc.)
    
    Supports pagination with configurable page size (default 50).
    """
    
    def get(self, request):
        """
        GET /api/admin/jobs/
        Returns paginated list of jobs with optional filters.
        
        Query parameters:
        - page: Page number (default 1)
        - page_size: Items per page (default 50)
        - status: Filter by job status
        - job_type: Filter by job type
        """
        # Start with all jobs
        queryset = Job.objects.all()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        job_type_filter = request.query_params.get('job_type')
        if job_type_filter:
            queryset = queryset.filter(job_type=job_type_filter)
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 50))
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        # Serialize data
        serializer = JobListSerializer(paginated_queryset, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)


class JobDetailView(APIView):
    """
    Returns detailed information for a specific job including logs.
    
    Provides complete job information with all log entries for monitoring
    and debugging background operations.
    """
    
    def get(self, request, pk):
        """
        GET /api/admin/jobs/{id}/
        Returns complete job information with logs.
        
        Path parameters:
        - pk: Job ID
        
        Returns:
        - 200: Job details with logs
        - 404: Job not found
        """
        try:
            # Fetch job with related logs using prefetch_related for optimization
            job = Job.objects.prefetch_related('logs').get(pk=pk)
        except Job.DoesNotExist:
            return Response(
                {'detail': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Import serializer here to avoid circular imports
        from api.serializers.jobs import JobDetailSerializer
        
        # Serialize and return job data
        serializer = JobDetailSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductListView(APIView):
    """
    Returns paginated list of products with filtering and sorting support.
    
    Supports filtering by:
    - title: Filter by product title (case-insensitive partial match)
    - vendor: Filter by vendor name (case-insensitive partial match)
    - product_type: Filter by product type (case-insensitive partial match)
    - tags: Filter by tags (case-insensitive partial match)
    
    Supports sorting by:
    - created_at: Sort by creation date (use -created_at for descending)
    - updated_at: Sort by update date (use -updated_at for descending)
    - title: Sort by title (use -title for descending)
    
    Supports pagination with configurable page size (default 50).
    """
    
    def get(self, request):
        """
        GET /api/admin/products/
        Returns paginated list of products with optional filters and sorting.
        
        Query parameters:
        - page: Page number (default 1)
        - page_size: Items per page (default 50, max 100)
        - title: Filter by product title
        - vendor: Filter by vendor name
        - product_type: Filter by product type
        - tags: Filter by tags
        - ordering: Sort field (created_at, updated_at, title, or prefix with - for descending)
        """
        # Start with all products, prefetch related data to avoid N+1 queries
        queryset = Product.objects.prefetch_related('variants', 'variants__inventory_item', 'variants__inventory_item__inventory_levels').all()
        
        # Apply filters
        title_filter = request.query_params.get('title')
        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)
        
        vendor_filter = request.query_params.get('vendor')
        if vendor_filter:
            queryset = queryset.filter(vendor__icontains=vendor_filter)
        
        product_type_filter = request.query_params.get('product_type')
        if product_type_filter:
            queryset = queryset.filter(product_type__icontains=product_type_filter)
        
        tags_filter = request.query_params.get('tags')
        if tags_filter:
            queryset = queryset.filter(tags__icontains=tags_filter)
        
        # Apply sorting
        ordering = request.query_params.get('ordering', '-created_at')
        # Validate ordering field to prevent SQL injection
        valid_orderings = ['created_at', '-created_at', 'updated_at', '-updated_at', 'title', '-title']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            # Default to descending created_at if invalid ordering provided
            queryset = queryset.order_by('-created_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        page_size = request.query_params.get('page_size', 50)
        try:
            page_size = int(page_size)
            # Limit page size to reasonable maximum
            if page_size > 100:
                page_size = 100
            elif page_size < 1:
                page_size = 50
        except (ValueError, TypeError):
            page_size = 50
        
        paginator.page_size = page_size
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        # Serialize data
        serializer = ProductListSerializer(paginated_queryset, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)



class ProductDetailView(APIView):
    """
    Returns detailed information for a specific product.
    
    Provides complete product information including nested images, variants,
    and inventory data. Uses select_related and prefetch_related for query
    optimization to avoid N+1 queries.
    
    Optimizations:
    - prefetch_related('images'): Fetch all images in one query
    - prefetch_related('variants'): Fetch all variants in one query
    - prefetch_related('variants__inventory_item'): Fetch inventory items
    - prefetch_related('variants__inventory_item__inventory_levels'): Fetch inventory levels
    """
    
    def get(self, request, pk):
        """
        GET /api/admin/products/{id}/
        Returns complete product information with variants, images, and inventory.
        
        Path parameters:
        - pk: Product ID
        
        Returns:
        - 200: Product details with nested data
        - 404: Product not found
        """
        try:
            # Fetch product with all related data using optimized queries
            # This prevents N+1 query problems by fetching all related data upfront
            product = Product.objects.prefetch_related(
                'images',  # Fetch all images
                'variants',  # Fetch all variants
                'variants__inventory_item',  # Fetch inventory items for variants
                'variants__inventory_item__inventory_levels'  # Fetch inventory levels
            ).get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize and return product data
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductSyncView(APIView):
    """
    Synchronizes a single product with Shopify.
    
    Calls the existing Product.export_to_shopify() method to create or update
    the product in Shopify, maintaining all business logic in the model layer.
    
    This endpoint delegates to existing business logic without duplication,
    following the design principle of keeping all sync logic in the model.
    """
    
    def post(self, request, pk):
        """
        POST /api/admin/products/{id}/sync/
        Synchronizes product with Shopify.
        
        Path parameters:
        - pk: Product ID
        
        Returns:
        - 200: Sync successful with results
        - 404: Product not found
        - 500: Sync failed with error details
        """
        try:
            # Fetch the product
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Call existing business logic to export product to Shopify
            # This method handles all sync operations including:
            # - Creating/updating product in Shopify
            # - Syncing variants
            # - Syncing images
            # - Updating inventory
            # - Updating local shopify_ids
            product.export_to_shopify()
            
            # Refresh product from database to get updated data
            product.refresh_from_db()
            
            # Return success response with sync results
            return Response(
                {
                    'success': True,
                    'message': 'Product synchronized successfully',
                    'synced_at': product.updated_at.isoformat() if product.updated_at else None,
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to sync product {pk}: {str(e)}", exc_info=True)
            
            # Return error response with details
            return Response(
                {
                    'success': False,
                    'message': 'Failed to sync product',
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductBulkSyncView(APIView):
    """
    Synchronizes multiple products with Shopify in bulk.
    
    Accepts an array of product IDs and processes each product individually,
    aggregating the results. Each product is synced using the existing
    Product.export_to_shopify() method to maintain business logic consistency.
    
    This endpoint provides batch processing capabilities while delegating
    to existing business logic without duplication.
    """
    
    def post(self, request):
        """
        POST /api/admin/products/bulk-sync/
        Synchronizes multiple products with Shopify.
        
        Request body:
        {
            "product_ids": [1, 2, 3, ...]
        }
        
        Returns:
        - 200: Bulk sync completed with aggregated results
        - 400: Invalid request (missing or invalid product_ids)
        
        Response format:
        {
            "success_count": 2,
            "error_count": 1,
            "results": [
                {"id": 1, "success": true},
                {"id": 2, "success": true},
                {"id": 3, "success": false, "error": "Error message"}
            ]
        }
        """
        # Validate request body
        product_ids = request.data.get('product_ids', [])
        
        if not isinstance(product_ids, list):
            return Response(
                {'detail': 'product_ids must be an array'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not product_ids:
            return Response(
                {'detail': 'product_ids array cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize counters and results
        success_count = 0
        error_count = 0
        results = []
        
        # Process each product
        for product_id in product_ids:
            try:
                # Validate product_id is an integer
                if not isinstance(product_id, int):
                    results.append({
                        'id': product_id,
                        'success': False,
                        'error': 'Invalid product ID format'
                    })
                    error_count += 1
                    continue
                
                # Fetch the product
                try:
                    product = Product.objects.get(pk=product_id)
                except Product.DoesNotExist:
                    results.append({
                        'id': product_id,
                        'success': False,
                        'error': 'Product not found'
                    })
                    error_count += 1
                    continue
                
                # Call existing business logic to export product to Shopify
                product.export_to_shopify()
                
                # Record success
                results.append({
                    'id': product_id,
                    'success': True
                })
                success_count += 1
                
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to sync product {product_id}: {str(e)}", exc_info=True)
                
                # Record failure
                results.append({
                    'id': product_id,
                    'success': False,
                    'error': str(e)
                })
                error_count += 1
        
        # Return aggregated results
        return Response(
            {
                'success_count': success_count,
                'error_count': error_count,
                'results': results
            },
            status=status.HTTP_200_OK
        )


class InventoryListView(APIView):
    """
    Returns paginated list of inventory items with filtering support.
    
    Only returns inventory items for variants with tracking enabled (tracked=True).
    
    Supports filtering by:
    - product_title: Filter by product title (case-insensitive partial match)
    - sku: Filter by SKU (case-insensitive partial match)
    
    Supports pagination with configurable page size (default 50).
    """
    
    def get(self, request):
        """
        GET /api/admin/inventory/
        Returns paginated list of inventory items with optional filters.
        
        Query parameters:
        - page: Page number (default 1)
        - page_size: Items per page (default 50, max 100)
        - product_title: Filter by product title
        - sku: Filter by SKU
        
        Returns only inventory items for tracked variants.
        """
        # Start with all inventory items for tracked variants
        # Use select_related to fetch variant and product in one query
        # Use prefetch_related to fetch inventory_levels efficiently
        queryset = InventoryItem.objects.filter(
            tracked=True
        ).select_related(
            'variant',
            'variant__product'
        ).prefetch_related(
            'inventory_levels'
        ).all()
        
        # Apply filters
        product_title_filter = request.query_params.get('product_title')
        if product_title_filter:
            queryset = queryset.filter(
                variant__product__title__icontains=product_title_filter
            )
        
        sku_filter = request.query_params.get('sku')
        if sku_filter:
            queryset = queryset.filter(
                shopify_sku__icontains=sku_filter
            )
        
        # Apply pagination
        paginator = PageNumberPagination()
        page_size = request.query_params.get('page_size', 50)
        try:
            page_size = int(page_size)
            # Limit page size to reasonable maximum
            if page_size > 100:
                page_size = 100
            elif page_size < 1:
                page_size = 50
        except (ValueError, TypeError):
            page_size = 50
        
        paginator.page_size = page_size
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        # Serialize data
        serializer = InventoryItemSerializer(paginated_queryset, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)


class InventoryReconcileView(APIView):
    """
    Reconciles inventory quantities with Shopify.
    
    Synchronizes all tracked inventory items with Shopify by pushing current
    source_quantity values to the default location. This operation ensures that
    local inventory data is synchronized with Shopify's inventory system.
    
    This endpoint delegates to the existing Shopify client's set_inventory_quantities
    method to maintain consistency with the rest of the system.
    """
    
    def post(self, request):
        """
        POST /api/admin/inventory/reconcile/
        Synchronizes inventory quantities with Shopify.
        
        Returns:
        - 200: Reconciliation successful with results
        - 500: Reconciliation failed with error details
        
        Response format:
        {
            "success": true,
            "reconciled_count": 45,
            "message": "Inventory reconciled successfully"
        }
        """
        try:
            # Get shop from session or request
            shop = getattr(request, 'shop', None)
            if not shop:
                return Response(
                    {'detail': 'Shop not found in session'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get session for API access
            from accounts.models import Session
            try:
                session = Session.objects.get(shop=shop)
            except Session.DoesNotExist:
                return Response(
                    {'detail': 'Session not found for shop'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Import Shopify client
            from shopify_client import ShopifyGraphQLClient
            from django.conf import settings
            
            # Create Shopify client
            client = ShopifyGraphQLClient(
                session.site,
                session.token,
                settings.API_VERSION,
            )
            
            # Get all tracked inventory items with their current quantities
            inventory_items = InventoryItem.objects.filter(
                tracked=True,
                source_quantity__isnull=False
            ).select_related(
                'variant',
                'variant__product'
            ).prefetch_related(
                'inventory_levels'
            ).all()
            
            # Build quantities array for Shopify API
            quantities = []
            reconciled_count = 0
            
            for inventory_item in inventory_items:
                # Get the inventory level for the default location
                inventory_level = inventory_item.inventory_levels.filter(
                    location_gid=settings.SHOPIFY_DEFAULT_LOCATION
                ).first()
                
                if inventory_level and inventory_item.source_quantity is not None:
                    # Construct GraphQL ID from shopify_id
                    # If shopify_id is not available, skip this item
                    if not inventory_item.shopify_id:
                        continue
                    
                    inventory_item_gid = f"gid://shopify/InventoryItem/{inventory_item.shopify_id}"
                    
                    # Add to quantities array for batch update
                    quantities.append({
                        'inventoryItemId': inventory_item_gid,
                        'locationId': settings.SHOPIFY_DEFAULT_LOCATION,
                        'quantities': [
                            {
                                'name': 'available',
                                'quantity': inventory_item.source_quantity
                            }
                        ]
                    })
                    reconciled_count += 1
            
            # If there are quantities to reconcile, push them to Shopify
            if quantities:
                errors = client.set_inventory_quantities(
                    name='Inventory Reconciliation',
                    reason='Reconciliation from Shop Manager',
                    quantities=quantities,
                    ignore_compare_quantity=False
                )
                
                if errors:
                    # Log errors but still return success with error details
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Inventory reconciliation errors: {errors}")
                    
                    return Response(
                        {
                            'success': False,
                            'reconciled_count': reconciled_count,
                            'message': 'Inventory reconciliation completed with errors',
                            'errors': errors
                        },
                        status=status.HTTP_200_OK
                    )
            
            # Return success response
            return Response(
                {
                    'success': True,
                    'reconciled_count': reconciled_count,
                    'message': 'Inventory reconciled successfully'
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to reconcile inventory: {str(e)}", exc_info=True)
            
            # Return error response with details
            return Response(
                {
                    'success': False,
                    'message': 'Failed to reconcile inventory',
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class SettingsView(APIView):
    """
    Returns and updates shop settings.
    
    Provides access to shop configuration including pricing configuration status
    and sync preferences. Allows updating sync preferences for the shop.
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
    """
    
    def get(self, request):
        """
        GET /api/admin/settings/
        Returns shop settings including pricing configuration and sync preferences.
        
        Returns:
        - 200: Shop settings
        - 404: Shop not found
        """
        # Get shop from session or request
        shop = getattr(request, 'shop', None)
        
        if not shop:
            return Response(
                {'detail': 'Shop not found in session'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build settings response
        settings_data = {
            'id': shop.id,
            'name': shop.name,
            'domain': shop.myshopify_domain,
            'currency': shop.currency,
            'pricing_config_enabled': getattr(shop, 'pricing_config_enabled', False),
            'sync_preferences': {
                'auto_sync_enabled': getattr(shop, 'auto_sync_enabled', False),
                'sync_frequency': getattr(shop, 'sync_frequency', 'daily'),
            }
        }
        
        return Response(settings_data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        PUT /api/admin/settings/
        Updates shop settings.
        
        Request body:
        {
            "sync_preferences": {
                "auto_sync_enabled": true,
                "sync_frequency": "daily"
            }
        }
        
        Returns:
        - 200: Settings updated successfully
        - 404: Shop not found
        - 400: Invalid request data
        """
        # Get shop from session or request
        shop = getattr(request, 'shop', None)
        
        if not shop:
            return Response(
                {'detail': 'Shop not found in session'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Extract sync preferences from request
            sync_preferences = request.data.get('sync_preferences', {})
            
            # Validate sync frequency if provided
            if 'sync_frequency' in sync_preferences:
                valid_frequencies = ['hourly', 'daily', 'weekly', 'manual']
                if sync_preferences['sync_frequency'] not in valid_frequencies:
                    return Response(
                        {
                            'detail': f"Invalid sync_frequency. Must be one of: {', '.join(valid_frequencies)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update shop settings
            if 'auto_sync_enabled' in sync_preferences:
                shop.auto_sync_enabled = sync_preferences['auto_sync_enabled']
            
            if 'sync_frequency' in sync_preferences:
                shop.sync_frequency = sync_preferences['sync_frequency']
            
            # Save shop
            shop.save()
            
            # Build updated settings response
            settings_data = {
                'id': shop.id,
                'name': shop.name,
                'domain': shop.myshopify_domain,
                'currency': shop.currency,
                'pricing_config_enabled': getattr(shop, 'pricing_config_enabled', False),
                'sync_preferences': {
                    'auto_sync_enabled': getattr(shop, 'auto_sync_enabled', False),
                    'sync_frequency': getattr(shop, 'sync_frequency', 'daily'),
                }
            }
            
            return Response(
                {
                    'success': True,
                    'message': 'Settings updated successfully',
                    'settings': settings_data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update settings: {str(e)}", exc_info=True)
            
            # Return error response with details
            return Response(
                {
                    'success': False,
                    'message': 'Failed to update settings',
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
