import hmac

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


def verificar_credencial_servicio(request):
    token_esperado = getattr(settings, "CATALOGO_SERVICIO_TOKEN", "")
    if not token_esperado:
        raise PermissionDenied("La credencial de servicio de Catálogo no está configurada.")

    token_recibido = request.headers.get("X-Service-Token", "")
    if not token_recibido:
        raise AuthenticationFailed("Falta la cabecera X-Service-Token.")

    if not hmac.compare_digest(token_recibido, token_esperado):
        raise PermissionDenied("Credencial de servicio inválida.")
