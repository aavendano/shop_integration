"""
Admin API URL configuration.
Endpoints for Shopify Polaris embedded UI.
"""
from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    # Context / session endpoint
    path('context/', views.ContextView.as_view(), name='context'),
    
    # Product endpoints
    path('products/', views.ProductListView.as_view(), name='product-list'),
    # path('products/<int:pk>/overview/', views.ProductOverviewView.as_view(), name='product-overview'),
    # path('products/<int:pk>/sync/', views.ProductSyncView.as_view(), name='product-sync'),
    # path('products/bulk-sync/', views.ProductBulkSyncView.as_view(), name='product-bulk-sync'),
    
    # Inventory endpoints (to be implemented in future tasks)
    # path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    # path('inventory/reconcile/', views.InventoryReconcileView.as_view(), name='inventory-reconcile'),
    
    # Order endpoints (to be implemented in future tasks)
    # path('orders/', views.OrderListView.as_view(), name='order-list'),
    # path('orders/<int:pk>/overview/', views.OrderOverviewView.as_view(), name='order-overview'),
    
    # Job endpoints
    path('jobs/', views.JobListView.as_view(), name='job-list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
]
