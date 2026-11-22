from rest_framework.response import Response
from rest_framework.views import exception_handler

from .mongo import CatalogoDBError


def manejador_excepciones(exc, context):
    if isinstance(exc, CatalogoDBError):
        return Response(
            {"error": {"codigo": "servicio_no_disponible", "mensaje": exc.mensaje}},
            status=503,
        )
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .mongo import CatalogoDBError


def manejador_excepciones(exc, context):
    if isinstance(exc, CatalogoDBError):
        return Response(
            {"error": {"codigo": "servicio_no_disponible", "mensaje": exc.mensaje}},
            status=503,
        )
    return exception_handler(exc, context)