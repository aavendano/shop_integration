from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, View, DetailView
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib import messages
from pathlib import Path
import tempfile
from .models import Supplier
from .forms import SupplierForm, ProductImportForm


class SupplierListView(ListView):
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'


class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = ProductImportForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProductImportForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES['product_data_file']

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            try:
                # Import the parsing functions
                from products_parsing.pipeline import load_records_from_json, run_pipeline

                # Load records from the CSV file
                records = load_records_from_json(tmp_path)

                # Determine config path based on supplier code
                config_path = Path(__file__).parent.parent / 'products_parsing' / \
                    'config' / 'providers' / f'{self.object.code}.json'

                if not config_path.exists():
                    messages.error(
                        request, f'Configuration file not found for supplier: {self.object.code}')
                    return self.render_to_response(self.get_context_data(import_form=form))

                # Get Shopify session (you'll need to implement this based on your auth setup)
                # For now, we'll assume there's a way to get the session
                from accounts.models import Session as ShopifySession
                session = ShopifySession.objects.first()

                if not session:
                    messages.error(
                        request, 'No Shopify session found. Please connect to Shopify first.')
                    return self.render_to_response(self.get_context_data(import_form=form))

                # Run the parsing pipeline
                summary, report = run_pipeline(
                    records=records,
                    config_path=str(config_path),
                    session=session
                )

                messages.success(
                    request,
                    f'Successfully imported products. '
                    f'Products - Created: {summary.products_created}, Updated: {summary.products_updated} | '
                    f'Variants - Created: {summary.variants_created}, Updated: {summary.variants_updated} | '
                    f'Errors: {len(report.errors)}'
                )

            except Exception as e:
                messages.error(request, f'Error importing products: {str(e)}')
            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

        else:
            messages.error(request, 'Invalid form submission')

        return redirect('suppliers:supplier_detail', pk=self.object.pk)


class SupplierCreateView(View):
    def get(self, request):
        form = SupplierForm()
        html = render_to_string('suppliers/partials/supplier_form.html',
                                {'form': form, 'title': 'Create Supplier'}, request=request)
        return HttpResponse(html)

    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            # If the submission was successful, we return a response (usually empty or with a trigger)
            # For simplicity, we can return a trigger to reload the page or update the list via HTMX.
            # Here we'll just redirect to the list view for a full reload as per the user's preference for a static list,
            # OR we can return a special header to tell HTMX to refresh.
            response = HttpResponse("")
            response['HX-Refresh'] = "true"
            return response

        # If invalid, re-render the form with errors
        html = render_to_string('suppliers/partials/supplier_form.html',
                                {'form': form, 'title': 'Create Supplier'}, request=request)
        return HttpResponse(html)


class SupplierUpdateView(View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(instance=supplier)
        html = render_to_string('suppliers/partials/supplier_form.html', {
                                'form': form, 'title': 'Edit Supplier', 'supplier': supplier}, request=request)
        return HttpResponse(html)

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            response = HttpResponse("")
            response['HX-Refresh'] = "true"
            return response

        html = render_to_string('suppliers/partials/supplier_form.html', {
                                'form': form, 'title': 'Edit Supplier', 'supplier': supplier}, request=request)
        return HttpResponse(html)


class SupplierDeleteView(View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        html = render_to_string(
            'suppliers/partials/supplier_confirm_delete.html', {'supplier': supplier}, request=request)
        return HttpResponse(html)

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.delete()
        response = HttpResponse("")
        response['HX-Refresh'] = "true"
        return response
