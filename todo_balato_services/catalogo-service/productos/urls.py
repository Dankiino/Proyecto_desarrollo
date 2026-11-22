
from django.urls import path

from .views import (
    HealthView,
    MongoHealthView,
    AdminVerificarView,
    AdminProductosView,
    AdminCategoriasView,
    AdminProductoDetalleView,
    ProductosPublicosView,
    AdminCategoriaDetalleView,
)

urlpatterns = [
    path("health", HealthView.as_view()),
    path("health/mongo", MongoHealthView.as_view()),
    path("admin/verificar", AdminVerificarView.as_view()),
    path("admin/productos", AdminProductosView.as_view()),
    path("admin/productos/<str:producto_id>", AdminProductoDetalleView.as_view()),
    path("admin/categorias", AdminCategoriasView.as_view()),
    path(
        "admin/categorias/<str:categoria_id>",
        AdminCategoriaDetalleView.as_view()
    ),
    path("productos", ProductosPublicosView.as_view()),

]
