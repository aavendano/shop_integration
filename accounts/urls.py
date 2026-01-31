from django.urls import path
from .views import (
    ShopListView, 
    ShopDetailView, 
    ShopCreateView, 
    ShopUpdateView, 
    ShopDeleteView, 
    ShopAuthView, 
    shopify_app_callback
    )

app_name = 'accounts'

urlpatterns = [
    path('shops/', ShopListView.as_view(), name='shop_list'),
    path('shops/add/', ShopCreateView.as_view(), name='shop_add'),
    path('shops/<int:pk>/', ShopDetailView.as_view(), name='shop_detail'),
    path('shops/<int:pk>/edit/', ShopUpdateView.as_view(), name='shop_update'),
    path('shops/<int:pk>/delete/', ShopDeleteView.as_view(), name='shop_delete'),
    path("shops/callback/", shopify_app_callback, name="shop_callback"),
    path("shops/<int:pk>/auth/", ShopAuthView.as_view(), name="shop_registration"),
]
