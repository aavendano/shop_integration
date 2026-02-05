from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', include('core.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('shopify_models/', include('shopify_models.urls')),
    path('prices/', include('prices.urls')),
    path('api/', include('api.urls')),  # API endpoints for Shopify Polaris UI
]

