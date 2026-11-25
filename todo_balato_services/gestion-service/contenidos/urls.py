from django.urls import path

from .views import ContenidosAdminView, ContenidosPublicosView, TemaActivoAdminView

urlpatterns = [
    path("contenidos", ContenidosPublicosView.as_view(), name="contenidos-publicos"),
    path("admin/contenidos", ContenidosAdminView.as_view(), name="contenidos-admin"),
    path("admin/tema-activo", TemaActivoAdminView.as_view(), name="tema-activo-admin"),
]
