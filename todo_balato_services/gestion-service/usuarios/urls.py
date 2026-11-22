from django.urls import path
from .views import (
    RegistroView, LoginView, LogoutView, MeView,
    UsuarioListView, BloquearUsuarioView, DesbloquearUsuarioView,
    ActivarCuentaView, ReenviarActivacionView,
    SolicitarRecuperacionView, RestablecerPasswordView,
)

urlpatterns = [
    path("registro", RegistroView.as_view()),
    path("activar", ActivarCuentaView.as_view()),
    path("activar/reenviar", ReenviarActivacionView.as_view()),
    path("recuperar-password", SolicitarRecuperacionView.as_view()),
    path("restablecer-password", RestablecerPasswordView.as_view()),
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("usuarios/me", MeView.as_view()),
    path("usuarios", UsuarioListView.as_view()),
    path("usuarios/<uuid:pk>/bloquear", BloquearUsuarioView.as_view()),
    path("usuarios/<uuid:pk>/desbloquear", DesbloquearUsuarioView.as_view()),
]