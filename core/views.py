
from django.shortcuts import render
from shopify_auth.decorators import login_required

@login_required
def home(request, *args, **kwargs):
    return render(request, "core/home.html")