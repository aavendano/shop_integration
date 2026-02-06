"""
Inventory serializers for API responses.

These serializers transform Django inventory models into render-ready JSON responses
for the Remix frontend. They provide inventory data formatted for UI display without
requiring additional transformation on the client.
"""

from rest_framework import serializers
from shopify_models.models import InventoryItem, InventoryLevel, Variant


class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory items with product and variant information.
    
    Provides inventory data including product title, variant title, SKU,
    source quantity, tracking status, and sync pending status.
    Formatted for direct consumption by Polaris IndexTable components.
    """
    
    product_title = serializers.SerializerMethodField()
    variant_title = serializers.SerializerMethodField()
    sku = serializers.CharField(source='shopify_sku', read_only=True)
    sync_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'product_title',
            'variant_title',
            'sku',
            'source_quantity',
            'tracked',
            'sync_pending',
        ]
    
    def get_product_title(self, obj):
        """
        Get the product title from the related variant's product.
        
        Returns the product title if the variant and product exist,
        otherwise returns None.
        """
        if obj.variant and obj.variant.product:
            return obj.variant.product.title
        return None
    
    def get_variant_title(self, obj):
        """
        Get the variant title from the related variant.
        
        Returns the variant title if it exists, otherwise returns None.
        """
        if obj.variant:
            return obj.variant.title
        return None
    
    def get_sync_pending(self, obj):
        """
        Determine if any inventory level for this item has sync_pending=True.
        
        Returns True if any inventory level has sync_pending flag set,
        indicating that inventory needs to be synchronized with Shopify.
        """
        return obj.inventory_levels.filter(sync_pending=True).exists()
