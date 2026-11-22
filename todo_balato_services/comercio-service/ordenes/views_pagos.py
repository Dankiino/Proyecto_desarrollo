import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.views import APIView

from . import pagos
from .permissions import EsClienteActivo

log = logging.getLogger(__name__)


def _error(e):
    return Response({"error": {"codigo": e.codigo, "mensaje": e.mensaje}}, status=e.status)


class IniciarPagoView(APIView):
    permission_classes = [EsClienteActivo]

    def post(self, request):
        try:
            url, token = pagos.iniciar_pago(request.data.get("orden_id"), request.user.id)
        except pagos.PagoError as e:
            return _error(e)
        return Response({"url": url, "token_ws": token})  # el navegador lo envía a Webpay


class ReverificarPagoView(APIView):
    permission_classes = [EsClienteActivo]

    def post(self, request, orden_id):
        try:
            orden = pagos.reverificar(orden_id, request.user.id)
        except pagos.PagoError as e:
            return _error(e)
        return Response({"orden": {"id": str(orden.id), "estado": orden.estado}})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def retorno_webpay(request):
    """Webpay devuelve aquí al cliente. Se verifica con Webpay y se redirige al frontend sin el token."""
    try:
        orden = pagos.procesar_retorno({**request.GET.dict(), **request.POST.dict()})
    except Exception as e:
        log.error("Retorno de Webpay falló: %s", type(e).__name__)
        orden = None
    destino = settings.FRONTEND_RESULT_URL
    return redirect(f"{destino}?{urlencode({'orden': orden.id})}" if orden else destino)
