from django.urls import path

from .views import (
    CategoriasView,
    HealthView,
    MongoHealthView,
    ProductoDetalleView,
    ProductosView,
)

urlpatterns = [
    path("health", HealthView.as_view()),
    path("health/mongo", MongoHealthView.as_view()),
    path("categorias", CategoriasView.as_view()),
    path("productos", ProductosView.as_view()),
    path("productos/<str:producto_id>", ProductoDetalleView.as_view()),
]