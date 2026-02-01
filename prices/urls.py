"""
Prices App URLs
"""

from django.urls import path
from . import views

app_name = 'prices'

urlpatterns = [
    # Pricing Setup
    path('setup/', views.PricingSetupView.as_view(), name='setup'),
    
    # Single Product Price Sync
    path('sync/<int:pk>/', views.ProductSyncPricesView.as_view(), name='sync_product'),
    
    # Bulk Price Sync
    path('bulk-sync/', views.BulkSyncPricesView.as_view(), name='bulk_sync'),
]
