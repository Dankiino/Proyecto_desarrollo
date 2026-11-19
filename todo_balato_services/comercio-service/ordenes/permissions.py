from rest_framework.permissions import BasePermission


class EsClienteActivo(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and getattr(u, "is_authenticated", False)
            and u.rol == "CLIENTE" and u.estado == "ACTIVO"
        )


class EsAdminActivo(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and getattr(u, "is_authenticated", False)
            and u.rol == "ADMIN" and u.estado == "ACTIVO"
        )