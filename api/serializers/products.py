"""
Product serializers for API responses.

These serializers transform Django models into render-ready JSON responses
for the Remix frontend. They follow the design specification to provide
UI-oriented data without requiring additional transformation on the client.
"""

from rest_framework import serializers
from shopify_models.models import Product, Variant, Image


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    
    Returns image data in a format ready for Polaris Thumbnail components.
    """
    
    class Meta:
        model = Image
        fields = ['id', 'src', 'position']


class VariantSerializer(serializers.ModelSerializer):
    """
    Serializer for product variants with inventory data.
    
    Includes inventory quantity from the related InventoryItem model,
    providing a complete view of variant data for UI display.
    """
    
    inventory_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Variant
        fields = [
            'id',
            'shopify_id',
            'title',
            'supplier_sku',
            'price',
            'compare_at_price',
            'barcode',
            'inventory_quantity',
            'inventory_policy',
            'option1',
            'option2',
            'option3',
        ]
    
    def get_inventory_quantity(self, obj):
        """
        Get inventory quantity from related InventoryItem.
        
        Returns None if no inventory item exists or quantity is not tracked.
        """
        if hasattr(obj, 'inventory_item') and obj.inventory_item:
            return obj.inventory_item.source_quantity
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view.
    
    Provides summary data optimized for IndexTable display in Polaris,
    including computed fields for variant count and sync status.
    """
    
    variant_count = serializers.SerializerMethodField()
    sync_status = serializers.SerializerMethodField()
    last_synced_at = serializers.DateTimeField(source='updated_at')
    
    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'vendor',
            'product_type',
            'tags',
            'variant_count',
            'sync_status',
            'last_synced_at',
            'created_at',
        ]
    
    def get_variant_count(self, obj):
        """
        Count the number of variants for this product.
        
        Uses prefetch_related optimization when available to avoid N+1 queries.
        """
        return obj.variants.count()
    
    def get_sync_status(self, obj):
        """
        Determine product sync status.
        
        Returns:
            - 'pending': Product not yet synced to Shopify (no shopify_id)
            - 'pending': Any variant has sync_pending inventory
            - 'synced': Product and all variants are synced
        """
        if not obj.shopify_id:
            return 'pending'
        
        # Check if any variant has pending inventory sync
        # Note: This checks InventoryLevel.sync_pending through the variant's inventory_item
        for variant in obj.variants.all():
            if hasattr(variant, 'inventory_item') and variant.inventory_item:
                inventory_item = variant.inventory_item
                # Check if any inventory level has sync_pending=True
                if inventory_item.inventory_levels.filter(sync_pending=True).exists():
                    return 'pending'
        
        return 'synced'


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail view.
    
    Provides complete product information including nested images and variants,
    formatted for direct consumption by Polaris Layout and Card components.
    """
    
    images = ImageSerializer(many=True, read_only=True)
    variants = VariantSerializer(many=True, read_only=True)
    sync_status = serializers.SerializerMethodField()
    last_synced_at = serializers.DateTimeField(source='updated_at')
    
    class Meta:
        model = Product
        fields = [
            'id',
            'shopify_id',
            'title',
            'description',
            'vendor',
            'product_type',
            'tags',
            'handle',
            'images',
            'variants',
            'sync_status',
            'last_synced_at',
        ]
    
    def get_sync_status(self, obj):
        """
        Determine product sync status.
        
        Returns:
            - 'pending': Product not yet synced to Shopify (no shopify_id)
            - 'pending': Any variant has sync_pending inventory
            - 'synced': Product and all variants are synced
        """
        if not obj.shopify_id:
            return 'pending'
        
        # Check if any variant has pending inventory sync
        for variant in obj.variants.all():
            if hasattr(variant, 'inventory_item') and variant.inventory_item:
                inventory_item = variant.inventory_item
                # Check if any inventory level has sync_pending=True
                if inventory_item.inventory_levels.filter(sync_pending=True).exists():
                    return 'pending'
        
        return 'synced'
