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
from api.serializers.products import ProductListSerializer
from shopify_models.models import Product


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
