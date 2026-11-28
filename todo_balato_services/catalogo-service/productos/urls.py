from django.urls import path

from .views import (
    HealthView,
    MongoHealthView,
    CategoriasView,
    ProductosView,
    ProductoDetalleView,
    AdminVerificarView,
    AdminProductosView,
    AdminCategoriasView,
    AdminProductoDetalleView,
    AdminCategoriaDetalleView,
    AdminAjustesInventarioView,
    InternoProductosConsultaView,
    InternoReservasView,
    InternoReservaDetalleView,
    InternoReservaConfirmarView,
    InternoReservaLiberarView,
)

urlpatterns = [
    # Estado del servicio
    path("health", HealthView.as_view()),
    path("health/mongo", MongoHealthView.as_view()),

    # Rutas públicas
    path("categorias", CategoriasView.as_view()),
    path("productos", ProductosView.as_view()),
    path(
        "productos/<str:producto_id>",
        ProductoDetalleView.as_view(),
    ),

    # Rutas administrativas
    path("admin/verificar", AdminVerificarView.as_view()),
    path("admin/productos", AdminProductosView.as_view()),
    path(
        "admin/productos/<str:producto_id>",
        AdminProductoDetalleView.as_view(),
    ),
    path("admin/categorias", AdminCategoriasView.as_view()),
    path(
        "admin/categorias/<str:categoria_id>",
        AdminCategoriaDetalleView.as_view(),
    ),
    path(
        "admin/productos/<str:producto_id>/ajustes",
        AdminAjustesInventarioView.as_view(),
    ),

    # Rutas internas de servicio (DEA-42)
    path(
        "interno/productos/consulta/",
        InternoProductosConsultaView.as_view(),
    ),
    path(
        "interno/reservas/",
        InternoReservasView.as_view(),
    ),
    path(
        "interno/reservas/<str:orden_id>/",
        InternoReservaDetalleView.as_view(),
    ),
    path(
        "interno/reservas/<str:orden_id>/confirmar/",
        InternoReservaConfirmarView.as_view(),
    ),
    path(
        "interno/reservas/<str:orden_id>/liberar/",
        InternoReservaLiberarView.as_view(),
    ),
]