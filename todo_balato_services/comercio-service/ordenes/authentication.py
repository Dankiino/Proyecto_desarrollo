from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings



class UsuarioRemoto:
    """Representa al usuario autenticado sin consultar una base local.
    Los datos vienen directo del payload del JWT emitido por Gestión."""

    def __init__(self, payload):
        self.id = payload.get("user_id")
        self.rol = payload.get("rol")
        self.estado = payload.get("estado")
        self.is_authenticated = True

    def __str__(self):
        return str(self.id)


class JWTRemotoAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # En vez de buscar en una base local, construimos el usuario
        # directamente desde el contenido del token.
        return UsuarioRemoto(validated_token)