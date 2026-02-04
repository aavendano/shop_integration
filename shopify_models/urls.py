from django.urls import path
from .views import (
    ProductListView, ProductDetailView, ProductSyncView,
    VariantCreateView, UpdateView, VariantUpdateView, VariantDeleteView,
    VariantAddLocationView
)

app_name = 'shopify_models'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/sync/', ProductSyncView.as_view(), name='product_sync'),

    # Variant CRUD
    path('products/<int:product_pk>/variants/create/',
         VariantCreateView.as_view(), name='variant_create'),
    path('products/<int:product_pk>/variants/<int:pk>/edit/',
         VariantUpdateView.as_view(), name='variant_update'),
    path('products/<int:product_pk>/variants/<int:pk>/delete/',
         VariantDeleteView.as_view(), name='variant_delete'),
    path('products/<int:product_pk>/variants/<int:pk>/add-location/',
         VariantAddLocationView.as_view(), name='variant_add_location'),
]
