import logging
import uuid

from django.db import transaction
from django.utils import timezone

from . import inventario, webpay
from .models import Orden, Pago

log = logging.getLogger(__name__)  # nunca se registra el token de Webpay


class PagoError(Exception):
    def __init__(self, status, codigo, mensaje):
        self.status, self.codigo, self.mensaje = status, codigo, mensaje


def iniciar_pago(orden_id, cliente_id):
    try:
        orden_id = uuid.UUID(str(orden_id))
    except ValueError:
        raise PagoError(404, "no_encontrado", "La orden no existe.")

    with transaction.atomic():
        orden = Orden.objects.select_for_update().filter(id=orden_id, cliente_id=cliente_id).first()
        if not orden:
            raise PagoError(404, "no_encontrado", "La orden no existe.")
        if orden.estado != "PENDIENTE_PAGO" or orden.moneda != "CLP":
            raise PagoError(409, "conflicto", "La orden no se puede pagar.")

        pago = Pago.objects.filter(orden=orden).first()
        if pago:  # doble clic o reintento: mismo intento de pago
            return pago.url_pago, pago.token_ws

        try:
            inventario.reservar(orden)
        except Exception:
            raise PagoError(503, "servicio_no_disponible", "No se pudo reservar el stock.")
        try:
            r = webpay.crear("O" + orden.id.hex[:25], str(orden.id), int(orden.total))
        except Exception as e:
            log.error("Webpay create falló orden=%s: %s", orden.id, type(e).__name__)
            raise PagoError(503, "servicio_no_disponible", "No se pudo iniciar el pago.")

        Pago.objects.create(orden=orden, token_ws=r["token"], url_pago=r["url"], buy_order="O" + orden.id.hex[:25])
        log.info("Pago iniciado orden=%s", orden.id)
        return r["url"], r["token"]


def procesar_retorno(params):
    """Retorno de Webpay: token_ws (pagó o rechazó) o TBK_TOKEN (canceló o expiró)."""
    cancelado = bool(params.get("TBK_TOKEN"))
    token = params.get("TBK_TOKEN") or params.get("token_ws")
    pago = Pago.objects.filter(token_ws=token).first() if token else None
    return _resolver(pago.id, cancelado) if pago else None


def reverificar(orden_id, cliente_id):
    pago = Pago.objects.filter(orden_id=orden_id, orden__cliente_id=cliente_id).first()
    if not pago:
        raise PagoError(404, "no_encontrado", "La orden no existe.")
    return _resolver(pago.id, False)


def _resolver(pago_id, cancelado):
    with transaction.atomic():
        pago = Pago.objects.select_for_update().select_related("orden").get(id=pago_id)
        if pago.estado in ("PENDIENTE", "POR_VERIFICAR"):
            _cancelar(pago) if cancelado else _verificar(pago)
        if pago.estado == "APROBADO" and pago.orden.estado == "CONFIRMACION_PENDIENTE":
            _consolidar(pago.orden)
        return pago.orden


def _verificar(pago):
    orden = pago.orden
    try:
        r = None
        if pago.estado == "POR_VERIFICAR":  # puede que el commit ya se haya hecho: no repetirlo
            r = webpay.consultar(pago.token_ws)
        if r is None or r.get("status") == "INITIALIZED":
            r = webpay.confirmar(pago.token_ws)
    except Exception as e:
        if "aborted" in str(e):  # Webpay cerró la transacción sin cobrar: no hay nada que reintentar
            return _cerrar(pago, "CANCELADO", "VENCIDA")
        log.error("Webpay no respondió orden=%s: %s", orden.id, type(e).__name__)
        pago.estado = "POR_VERIFICAR"
        pago.save()
        return

    if r.get("status") != "AUTHORIZED" or r.get("response_code") != 0:
        return _cerrar(pago, "RECHAZADO", "RECHAZADA")
    if r.get("buy_order") != pago.buy_order or int(r.get("amount", -1)) != int(orden.total):
        log.error("Pago inconsistente orden=%s", orden.id)  # cobrado pero no coincide: revisión, sin confirmar
        pago.estado, orden.estado = "INCONSISTENTE", "REVISION_REQUERIDA"
        pago.save(), orden.save()
        return

    # Webpay Plus opera solo en CLP; la orden se valida en CLP al iniciar el pago.
    pago.estado, pago.monto_verificado, pago.moneda_verificada = "APROBADO", orden.total, orden.moneda
    orden.estado = "CONFIRMACION_PENDIENTE"
    pago.save(), orden.save()


def _cancelar(pago):
    _cerrar(pago, "CANCELADO", "CANCELADA")


def _cerrar(pago, estado_pago, estado_orden):
    pago.estado, pago.orden.estado = estado_pago, estado_orden
    pago.save(), pago.orden.save()
    try:
        inventario.liberar(pago.orden)
    except Exception as e:
        log.error("No se pudo liberar stock orden=%s: %s", pago.orden.id, type(e).__name__)


def _consolidar(orden):
    try:
        inventario.consolidar(orden)
    except Exception as e:
        log.error("No se pudo consolidar stock orden=%s: %s", orden.id, type(e).__name__)
        return  # queda CONFIRMACION_PENDIENTE y se reintenta al revisar de nuevo
    orden.estado, orden.confirmada_en = "CONFIRMADA", timezone.now()
    orden.save()
    log.info("Orden confirmada orden=%s", orden.id)
