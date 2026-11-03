from rest_framework.permissions import BasePermission


class EsAdminActivo(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rol == "ADMIN" and u.estado == "ACTIVO")


class EsClienteActivo(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rol == "CLIENTE" and u.estado == "ACTIVO")