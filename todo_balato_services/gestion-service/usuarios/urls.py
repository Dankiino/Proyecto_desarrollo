from django.urls import path
from .views import (
    RegistroView, LoginView, LogoutView, MeView,
    UsuarioListView, BloquearUsuarioView, DesbloquearUsuarioView,
)

urlpatterns = [
    path("registro", RegistroView.as_view()),
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("usuarios/me", MeView.as_view()),
    path("usuarios", UsuarioListView.as_view()),
    path("usuarios/<uuid:pk>/bloquear", BloquearUsuarioView.as_view()),
    path("usuarios/<uuid:pk>/desbloquear", DesbloquearUsuarioView.as_view()),
]