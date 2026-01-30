import requests
from django.core.cache import cache
from django.http import HttpResponseBadRequest, HttpResponse
import hashlib
import hmac
import secrets
import urllib.parse
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect

from django.views.generic import RedirectView, ListView, DetailView, CreateView, UpdateView, DeleteView

from django.urls import reverse_lazy
from .models import Shop
from .forms import ShopForm


class ShopAuthView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        shop = Shop.objects.get(pk=kwargs['pk'])
        if not shop or not shop.myshopify_domain.endswith(".myshopify.com"):
            return HttpResponseBadRequest("Missing or invalid 'shop' parameter")

        # Generar un state aleatorio y guardarlo en el cache
        state = secrets.token_urlsafe(16)
        cache.set(f"shopify_oauth_state_{shop.myshopify_domain}", state, timeout=600)

        params = {
            "client_id": shop.client_id,
            "scope": "read_products,write_products",
            "redirect_uri": "https://" + self.request.get_host() + reverse_lazy('accounts:shop_callback'),
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)

        install_url = f"https://{shop.myshopify_domain}/admin/oauth/authorize?{query_string}"

        return install_url

def shopify_app_install(request):
    shop_domain = request.GET.get("shop")

    # Validación básica del parámetro shop
    if not shop_domain or not shop_domain.endswith(".myshopify.com"):
        return HttpResponseBadRequest("Missing or invalid 'shop' parameter")

    try:
        shop = Shop.objects.get(myshopify_domain=shop_domain)
    except Shop.DoesNotExist:
        return HttpResponseBadRequest(f"Shop {shop_domain} not registered in the system.")

    # Generar un state aleatorio y guardarlo en el cache
    state = secrets.token_urlsafe(16)
    cache.set(f"shopify_oauth_state_{shop_domain}", state, timeout=600)
    
    # Construir la URL de autorización de Shopify
    params = {
        "client_id": shop.client_id,
        "scope": "read_products,write_products",
        "redirect_uri": "https://" + request.get_host() + reverse_lazy('accounts:shop_callback'),
        "state": state,
    }
    query_string = urllib.parse.urlencode(params)
    install_url = f"https://{shop_domain}/admin/oauth/authorize?{query_string}"

    return redirect(install_url)


# apps/shopify_auth/views.py


def verify_hmac(params: dict, client_secret: str) -> bool:
    """
    Verifica el HMAC de la query de Shopify.
    params: request.GET dict-like (QueryDict → conviene convertir a dict simple)
    """
    # Extraer hmac de los parámetros
    hmac_from_shopify = params.get("hmac")
    if not hmac_from_shopify:
        return False

    # Crear un dict sin 'hmac'
    params_excl_hmac = {k: v for k, v in params.items() if k != "hmac"}

    # Ordenar alfabéticamente y codificar
    message = "&".join(
        f"{k}={','.join(sorted(v)) if isinstance(v, list) else v}"
        for k, v in sorted(params_excl_hmac.items())
    )

    # Calcular HMAC con client_secret
    digest = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Comparar en tiempo constante
    return hmac.compare_digest(digest, hmac_from_shopify)


def exchange_code_for_access_token(shop: str, code: str, client_id: str, client_secret: str) -> str:
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # data = {"access_token": "...", "scope": "read_products,write_products,..."}
    return data["access_token"]


from django.contrib import messages

def shopify_app_callback(request):
    """
    Callback de OAuth.
    Shopify redirige aquí con ?code=...&shop=...&state=...&hmac=...
    """
    params = request.GET.copy()  # QueryDict

    shop_domain = params.get("shop")
    code = params.get("code")
    state = params.get("state")

    if not shop_domain or not code or not state:
        return HttpResponseBadRequest("Faltan parámetros requeridos")

    try:
        shop_obj = Shop.objects.get(myshopify_domain=shop_domain)
    except Shop.DoesNotExist:
        return HttpResponseBadRequest("Tienda no encontrada")

    # Verificar 'state' usando cache
    expected_state = cache.get(f"shopify_oauth_state_{shop_domain}")
    if not expected_state or expected_state != state:
        return HttpResponseBadRequest("State inválido")
    
    # Eliminar el state una vez usado
    cache.delete(f"shopify_oauth_state_{shop_domain}")

    # Verificar HMAC con el client_secret de la tienda
    if not verify_hmac(params, shop_obj.client_secret):
        return HttpResponseBadRequest("Firma HMAC inválida")

    # Intercambiar 'code' por access_token usando los credenciales de la tienda
    try:
        access_token = exchange_code_for_access_token(
            shop_domain, code, shop_obj.client_id, shop_obj.client_secret
        )
    except Exception as e:
        return HttpResponse(f"Error al obtener token: {str(e)}", status=500)

    # Guardar/Actualizar la sesión vinculada a la tienda
    from .models import Session
    Session.objects.update_or_create(
        shop=shop_obj,
        defaults={
            'site': shop_domain,
            'token': access_token,
        }
    )

    shop_obj.is_authentified = True
    shop_obj.save()

    messages.success(request, f'Instalación completada exitosamente para {shop_domain}.')
    return redirect('core:home')


class ShopListView(ListView):
    model = Shop
    template_name = 'accounts/shop_list.html'
    context_object_name = 'shops'


class ShopDetailView(DetailView):
    model = Shop
    template_name = 'accounts/shop_detail.html'
    context_object_name = 'shop'


class ShopCreateView(CreateView):
    model = Shop
    form_class = ShopForm
    template_name = 'accounts/shop_form.html'
    success_url = reverse_lazy('accounts:shop_list')


class ShopUpdateView(UpdateView):
    model = Shop
    form_class = ShopForm
    template_name = 'accounts/shop_form.html'
    success_url = reverse_lazy('accounts:shop_list')


class ShopDeleteView(DeleteView):
    model = Shop
    template_name = 'accounts/shop_confirm_delete.html'
    success_url = reverse_lazy('accounts:shop_list')
