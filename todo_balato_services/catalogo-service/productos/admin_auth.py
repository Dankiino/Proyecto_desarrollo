
import os
import json
import urllib.error
import urllib.request

from django.conf import settings
from rest_framework.exceptions import (
    AuthenticationFailed,
    PermissionDenied,
    APIException,
)


class GestionNoDisponible(APIException):
    status_code = 503
    default_detail = "No se pudo verificar el usuario con Gestión."
    default_code = "gestion_no_disponible"


def verificar_admin(request):
    """
    Consulta a Gestión para validar el JWT y los permisos.
    No confía en los datos enviados por el frontend.
    """

    autorizacion = request.headers.get("Authorization", "")

    if not autorizacion.startswith("Bearer "):
        raise AuthenticationFailed("Debes iniciar sesión.")

    token = autorizacion[7:].strip()

    if not token:
        raise AuthenticationFailed("Token no proporcionado.")

    gestion_url = os.environ.get(
        "GESTION_API_URL",
        "http://127.0.0.1:8000/api"
    ).rstrip("/")


    peticion = urllib.request.Request(
        f"{gestion_url}/usuarios/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            usuario = json.load(respuesta)

    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise AuthenticationFailed(
                "La sesión no es válida o ha expirado."
            )
        raise GestionNoDisponible()

    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
    ):
        raise GestionNoDisponible()

    if not isinstance(usuario, dict):
        raise GestionNoDisponible()

    if (
        usuario.get("rol") != "ADMIN"
        or usuario.get("estado") != "ACTIVO"
    ):
        raise PermissionDenied(
            "No tienes permisos para administrar el catálogo."
        )

    return usuario
