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

# Dashboard Views for Session CRUD


class SessionListView(LoginRequiredMixin, generic.ListView):
    model = Session
    template_name = 'session/session_list.html'
    context_object_name = 'sessions'


class SessionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Session
    fields = ['site', 'token']
    template_name = 'session/session_form.html'
    success_url = reverse_lazy('core:session_list')


class SessionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Session
    fields = ['site', 'token']
    template_name = 'session/session_form.html'
    success_url = reverse_lazy('core:session_list')


class SessionDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Session
    template_name = 'session/session_confirm_delete.html'
    success_url = reverse_lazy('core:session_list')


def home(request, *args, **kwargs):
    return render(request, "core/home.html")
