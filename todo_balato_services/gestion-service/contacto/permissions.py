
from rest_framework.permissions import BasePermission


class EsAdminContacto(BasePermission):
    message = "No tienes permiso para consultar los mensajes de contacto."

    def has_permission(self, request, view):
        usuario = request.user

        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol == "ADMIN"
            and usuario.estado == "ACTIVO"
            and usuario.is_active
        )
