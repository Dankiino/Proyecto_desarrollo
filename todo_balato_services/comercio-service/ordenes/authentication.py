import requests
from django.conf import settings
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class IdentidadNoDisponible(exceptions.APIException):
    status_code = 503
    default_detail = "No se pudo verificar la sesión."
    default_code = "identidad_no_disponible"


class UsuarioRemoto:
    """Usuario autenticado según Gestión (sin base local)."""

    def __init__(self, datos):
        self.id = datos["id"]
        self.rol = datos["rol"]
        self.estado = datos["estado"]
        self.is_authenticated = True

    def __str__(self):
        return str(self.id)


class JWTRemotoAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # El rol y el estado del token pueden estar desactualizados (p. ej. cuenta bloqueada
        # después de emitirlo): se consultan a Gestión, que rechaza si la cuenta no está activa.
        try:
            r = requests.get(
                f"{settings.GESTION_URL}/api/usuarios/me",
                headers={"Authorization": f"Bearer {validated_token}"},
                timeout=3,
            )
        except requests.RequestException:
            raise IdentidadNoDisponible()
        if r.status_code in (401, 403):
            raise exceptions.AuthenticationFailed("Sesión inválida o cuenta no activa.")
        if r.status_code != 200:
            raise IdentidadNoDisponible()
        return UsuarioRemoto(r.json())
