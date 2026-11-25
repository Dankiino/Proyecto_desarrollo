from rest_framework.permissions import BasePermission


class EsAdminContenidos(BasePermission):
    """Permite administrar contenidos solo a cuentas ADMIN activas."""

    message = "Esta cuenta no está autorizada para administrar contenidos."

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and u.is_active
            and getattr(u, "rol", None) == "ADMIN"
            and getattr(u, "estado", None) == "ACTIVO"
        )
