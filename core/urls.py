# urls.py
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/add/', views.SessionCreateView.as_view(), name='session_add'),
    path('sessions/<int:pk>/edit/', views.SessionUpdateView.as_view(), name='session_edit'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
]


