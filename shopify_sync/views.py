from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from .models import Product, Variant
from .filters import ProductFilter
from .forms import VariantForm


class ProductListView(FilterView):
    model = Product
    template_name = 'shopify_sync/product_list.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 50
    
    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')


class ProductDetailView(DetailView):
    model = Product
    template_name = 'shopify_sync/product_detail.html'
    context_object_name = 'product'


class VariantCreateView(CreateView):
    model = Variant
    form_class = VariantForm
    template_name = 'shopify_sync/variant_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        form.instance.product = product
        form.instance.session = product.session
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('shopify_sync:product_detail', kwargs={'pk': self.kwargs['product_pk']})


class VariantUpdateView(UpdateView):
    model = Variant
    form_class = VariantForm
    template_name = 'shopify_sync/variant_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        context['action'] = 'Edit'
        return context
    
    def get_success_url(self):
        return reverse_lazy('shopify_sync:product_detail', kwargs={'pk': self.kwargs['product_pk']})


class VariantDeleteView(DeleteView):
    model = Variant
    template_name = 'shopify_sync/variant_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        return context
    
    def get_success_url(self):
        return reverse_lazy('shopify_sync:product_detail', kwargs={'pk': self.kwargs['product_pk']})
