"""
URL configuration for webhook endpoints.
"""
from django.urls import path
from . import views

app_name = 'webhooks'

urlpatterns = [
    # Shopify app webhooks
    path('app/uninstalled/', views.app_uninstalled_webhook, name='app-uninstalled'),
    path('app/scopes_update/', views.scopes_update_webhook, name='app-scopes-update'),
]
