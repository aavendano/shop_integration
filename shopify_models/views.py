import logging
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django_filters.views import FilterView
from .models import Product, Variant
from .filters import ProductFilter
from .forms import VariantForm

logger = logging.getLogger(__name__)


class ProductListView(FilterView):
    model = Product
    template_name = 'shopify_models/product_list.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 50

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')


class ProductDetailView(DetailView):
    model = Product
    template_name = 'shopify_models/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Get all images ordered by position
        context['images'] = product.images.all().order_by('position')
        
        # Get variants with their related inventory data
        from .models import Location, InventoryItem
        
        variants_data = []
        for variant in product.variants.all().order_by('position'):
            variant_info = {
                'variant': variant,
                'inventory_item': None,
                'inventory_levels': []
            }
            
            # Get inventory item if it exists
            if hasattr(variant, 'inventory_item') and variant.inventory_item:
                variant_info['inventory_item'] = variant.inventory_item
                # Get inventory levels for this item
                variant_info['inventory_levels'] = variant.inventory_item.inventory_levels.select_related('inventory_item').all()
            
            variants_data.append(variant_info)
        
        context['variants_data'] = variants_data
        
        # Get all available locations
        context['locations'] = Location.objects.all().order_by('name')
        
        return context



class ProductSyncView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            # Check if the export method exists
            if not hasattr(product, 'export_to_shopify'):
                raise AttributeError(
                    f"Product model does not have 'export_to_shopify' method. "
                    f"Available methods: {[m for m in dir(product) if not m.startswith('_')]}"
                )
            
            # Export product and its children to Shopify
            product.export_to_shopify()
            messages.success(
                request, f'Product "{product.title}" synchronized successfully with Shopify.')
        except AttributeError as e:
            # Log the full traceback for AttributeError (missing methods/attributes)
            logger.exception(
                f"AttributeError while synchronizing product {pk} ('{product.title}'): {str(e)}"
            )
            messages.error(
                request, 
                f'Failed to synchronize product "{product.title}": Method not implemented. '
                f'Check server logs for details.'
            )
        except Exception as e:
            # Log the full traceback for any other exception
            logger.exception(
                f"Unexpected error while synchronizing product {pk} ('{product.title}'): {str(e)}"
            )
            messages.error(
                request, 
                f'Failed to synchronize product "{product.title}": {str(e)}. '
                f'Check server logs for full traceback.'
            )

        return redirect('shopify_models:product_detail', pk=pk)


class VariantCreateView(CreateView):
    model = Variant
    form_class = VariantForm
    template_name = 'shopify_models/variant_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            Product, pk=self.kwargs['product_pk'])
        context['action'] = 'Create'
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        form.instance.product = product
        form.instance.session = product.session
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('shopify_models:product_detail', kwargs={'pk': self.kwargs['product_pk']})


class VariantUpdateView(UpdateView):
    model = Variant
    form_class = VariantForm
    template_name = 'shopify_models/variant_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            Product, pk=self.kwargs['product_pk'])
        context['action'] = 'Edit'
        return context

    def get_success_url(self):
        return reverse_lazy('shopify_models:product_detail', kwargs={'pk': self.kwargs['product_pk']})


class VariantDeleteView(DeleteView):
    model = Variant
    template_name = 'shopify_models/variant_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            Product, pk=self.kwargs['product_pk'])
        return context

    def get_success_url(self):
        return reverse_lazy('shopify_models:product_detail', kwargs={'pk': self.kwargs['product_pk']})
