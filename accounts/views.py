import json
import requests
from django.core.cache import cache
from django.http import HttpResponseBadRequest, HttpResponse
import hashlib
import hmac
from django.shortcuts import render

# Create your views here.
# apps/shopify_auth/views.py
import secrets
import urllib.parse

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache  # o tu propio storage para 'state'


def shopify_install(request):
    """
    Inicia el flujo OAuth.
    Espera un parámetro GET ?shop=mi-tienda.myshopify.com
    """
    shop = request.GET.get("shop")
    if not shop:
        return HttpResponseBadRequest("Falta parámetro 'shop'")

    # Validas que sea tu tienda concreta si quieres:
    # if shop != "mi-tienda.myshopify.com": ...

    # Generar 'state' aleatorio para prevenir CSRF
    state = secrets.token_urlsafe(16)
    # Guardar 'state' temporalmente (cache, session, DB)
    cache.set(f"shopify_oauth_state_{shop}", state, timeout=600)

    params = {
        "client_id": settings.SHOPIFY_CLIENT_ID,
        "scope": settings.SHOPIFY_APP_SCOPES,
        "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
        "state": state,
    }
    query = urllib.parse.urlencode(params)
    # URL a Shopify para pedir permisos
    redirect_url = f"https://{shop}/admin/oauth/authorize?{query}"

    return redirect(redirect_url)


# apps/shopify_auth/views.py


def verify_hmac(params: dict) -> bool:
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
        settings.SHOPIFY_CLIENT_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Comparar en tiempo constante
    return hmac.compare_digest(digest, hmac_from_shopify)


def exchange_code_for_access_token(shop: str, code: str) -> str:
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": settings.SHOPIFY_CLIENT_ID,
        "client_secret": settings.SHOPIFY_CLIENT_SECRET,
        "code": code,
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # data = {"access_token": "...", "scope": "read_products,write_products,..."}
    return data["access_token"]


def shopify_callback(request):
    """
    Callback de OAuth.
    Shopify redirige aquí con ?code=...&shop=...&state=...&hmac=...
    """
    params = request.GET.copy()  # QueryDict

    shop = params.get("shop")
    code = params.get("code")
    state = params.get("state")

    if not shop or not code or not state:
        return HttpResponseBadRequest("Faltan parámetros requeridos")

    # Verificar 'state'
    expected_state = cache.get(f"shopify_oauth_state_{shop}")
    if not expected_state or expected_state != state:
        return HttpResponseBadRequest("State inválido")

    # (Opcional pero muy recomendable) Verificar HMAC
    if not verify_hmac(params):
        return HttpResponseBadRequest("Firma HMAC inválida")

    # Intercambiar 'code' por access_token
    access_token = exchange_code_for_access_token(shop, code)

    # Guardar 'access_token' en DB/config; como es una sola tienda,
    # puedes guardarlo en un modelo SiteConfig o similar
    from .models import Session  # ejemplo
    Session.objects.update_or_create(
        site=shop,
        token=access_token,
    )

    return HttpResponse("Instalación completada. Token guardado.")
