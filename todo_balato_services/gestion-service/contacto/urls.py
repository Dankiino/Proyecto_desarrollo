
from django.urls import path

from .views import (
    CrearMensajeContactoView,
    ListarMensajesContactoView,
    DetalleMensajeContactoView,
)

urlpatterns = [
    path(
        "contacto/",
        CrearMensajeContactoView.as_view(),
        name="crear-contacto",
    ),
    path(
        "admin/contacto/",
        ListarMensajesContactoView.as_view(),
        name="listar-contacto",
    ),
    path(
        "admin/contacto/<int:pk>/",
        DetalleMensajeContactoView.as_view(),
        name="detalle-contacto",
    ),
]
