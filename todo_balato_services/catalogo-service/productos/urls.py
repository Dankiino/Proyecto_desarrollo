from django.urls import path

from .views import (
    HealthView,
    MongoHealthView,
    ProductosView,
    ProductoDetalleView,
    CategoriasView,
)

urlpatterns = [
    # Comprobación del servicio
    path("health", HealthView.as_view()),
    path("health/mongo", MongoHealthView.as_view()),

    # Catálogo público
    path("productos", ProductosView.as_view()),
    path("productos/<str:producto_id>", ProductoDetalleView.as_view()),
    path("categorias", CategoriasView.as_view()),
]
