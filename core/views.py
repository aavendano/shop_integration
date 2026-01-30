from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from accounts.models import Session

# Authentication Views


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:home')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('core:login')


def home(request, *args, **kwargs):
    return render(request, "core/home.html")
