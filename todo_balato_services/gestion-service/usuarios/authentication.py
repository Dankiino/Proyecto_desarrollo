from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTActivoAuthentication(JWTAuthentication):
    """Consulta el estado real del usuario en cada solicitud: un token emitido antes
    del bloqueo deja de servir de inmediato."""

    def get_user(self, validated_token):
        usuario = super().get_user(validated_token)
        if usuario.estado != "ACTIVO":
            raise AuthenticationFailed("Cuenta no activa", code="user_inactive")
        return usuario
