"""
URL configuration for the API app.
All API endpoints are namespaced under /api/admin/
Webhook endpoints are under /webhooks/
"""
from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # Admin API endpoints for Shopify Polaris UI
    path('admin/', include('api.admin.urls')),
    
    # Webhook endpoints for Shopify app events
    path('webhooks/', include('api.webhooks.urls')),
]
