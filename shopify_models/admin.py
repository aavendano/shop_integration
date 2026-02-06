from django.contrib import admin
from .models import Market, Publication, PriceList, Catalog, Product
from .sync import sync_market, sync_publication, sync_price_list, sync_catalog


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'handle', 'enabled', 'primary', 'currency', 'shopify_id']
    list_filter = ['enabled', 'primary', 'currency']
    search_fields = ['name', 'handle', 'shopify_id']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            sync_market(obj)
            self.message_user(request, f"Market '{obj.name}' synced successfully with Shopify.")
        except Exception as e:
            self.message_user(request, f"Error syncing market: {str(e)}", level='error')


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'auto_publish', 'shopify_id', 'created_at']
    list_filter = ['auto_publish']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            sync_publication(obj)
            self.message_user(request, f"Publication synced successfully with Shopify.")
        except Exception as e:
            self.message_user(request, f"Error syncing publication: {str(e)}", level='error')


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'shopify_id', 'created_at']
    list_filter = ['currency']
    search_fields = ['name', 'shopify_id']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            sync_price_list(obj)
            self.message_user(request, f"Price List '{obj.name}' synced successfully with Shopify.")
        except Exception as e:
            self.message_user(request, f"Error syncing price list: {str(e)}", level='error')


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'market', 'publication', 'price_list', 'shopify_id']
    list_filter = ['status']
    search_fields = ['title', 'shopify_id']
    raw_id_fields = ['market', 'publication', 'price_list']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            sync_catalog(obj, create_dependencies=True)
            self.message_user(request, f"Catalog '{obj.title}' synced successfully with Shopify.")
        except Exception as e:
            self.message_user(request, f"Error syncing catalog: {str(e)}", level='error')
