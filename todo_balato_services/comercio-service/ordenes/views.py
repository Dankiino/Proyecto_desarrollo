import logging
import uuid
from decimal import Decimal
from django.db import DatabaseError, IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . import inventario
from .catalogo_client import (
    CatalogoNoDisponibleError,
    ProductoNoEncontradoError,
    RespuestaCatalogoInvalidaError,
    obtener_producto,
)
from .models import DetalleOrden, Orden
from .permissions import EsClienteActivo

log = logging.getLogger(__name__)


def _error_validacion(campo, mensaje):
    return Response(
        {
            "error": {
                "codigo": "validacion",
                "mensaje": "Los datos enviados no son válidos.",
                "campos": {campo: [mensaje]},
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _validar_items(items):
    if not isinstance(items, list) or not items:
        return _error_validacion("items", "El carrito debe contener al menos un producto.")

    productos_vistos = set()
    for indice, item in enumerate(items):
        campo = f"items[{indice}]"
        if not isinstance(item, dict):
            return _error_validacion(campo, "Cada producto debe ser un objeto.")

        producto_id = item.get("producto_id")
        if not isinstance(producto_id, str) or not producto_id.strip():
            return _error_validacion(f"{campo}.producto_id", "Debe indicar un producto válido.")
        if producto_id in productos_vistos:
            return _error_validacion(
                f"{campo}.producto_id",
                "El producto está repetido; envíe una sola línea por producto.",
            )
        productos_vistos.add(producto_id)

        cantidad = item.get("cantidad")
        if type(cantidad) is not int or cantidad <= 0:
            return _error_validacion(
                f"{campo}.cantidad",
                "La cantidad debe ser un número entero mayor que cero.",
            )

    return None


def _coincide_con_orden(orden, cliente_id, items):
    if str(orden.cliente_id) != str(cliente_id):
        return False

    cantidades_pedidas = {
        item["producto_id"]: item["cantidad"]
        for item in items
    }
    cantidades_guardadas = {
        linea.producto_id: linea.cantidad
        for linea in orden.lineas.all()
    }
    return cantidades_pedidas == cantidades_guardadas


def _conflicto_idempotencia():
    return Response(
        {
            "error": {
                "codigo": "conflicto",
                "mensaje": "La clave Idempotency-Key ya se usó para otro pedido.",
            }
        },
        status=status.HTTP_409_CONFLICT,
    )


def calcular_lineas(items):
    lineas = []
    total = 0
    puede_pagar = True

    for item in items:
        producto_id = item.get("producto_id")
        cantidad = item.get("cantidad", 0)

        try:
            producto = obtener_producto(producto_id)
        except ProductoNoEncontradoError:
            lineas.append({
                "producto_id": producto_id,
                "nombre": None,
                "precio_unitario": None,
                "cantidad": cantidad,
                "subtotal": 0,
                "problema": "no_existe",
            })
            puede_pagar = False
            continue

        stock_disponible = producto.get("stock_disponible", 0)
        problema = None
        if stock_disponible <= 0:
            problema = "agotado"
        elif cantidad > stock_disponible:
            problema = "stock_insuficiente"

        precio = producto.get("precio", 0)
        subtotal = precio * cantidad if not problema else 0

        lineas.append({
            "producto_id": producto_id,
            "nombre": producto.get("nombre"),
            "precio_unitario": precio,
            "cantidad": cantidad,
            "subtotal": subtotal,
            "problema": problema,
        })

        if problema:
            puede_pagar = False
        else:
            total += subtotal

    return lineas, total, puede_pagar


class CarritoCalcularView(APIView):
    permission_classes = []  # público, carrito anónimo
    authentication_classes = []

    def post(self, request):
        items = request.data.get("items", [])
        error = _validar_items(items)
        if error:
            return error

        try:
            lineas, total, puede_pagar = calcular_lineas(items)
        except CatalogoNoDisponibleError as exc:
            return Response(
                {"error": {"codigo": "catalogo_no_disponible", "mensaje": str(exc)}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RespuestaCatalogoInvalidaError as exc:
            return Response(
                {"error": {"codigo": "respuesta_catalogo_invalida", "mensaje": str(exc)}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            "moneda": "CLP",
            "lineas": lineas,
            "total": total,
            "puede_pagar": puede_pagar,
        })


class CheckoutView(APIView):
    permission_classes = [EsClienteActivo]

    def post(self, request):
        items = request.data.get("items", [])
        total_esperado = request.data.get("total_esperado")
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {"error": {"codigo": "validacion", "mensaje": "Falta la cabecera Idempotency-Key."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(idempotency_key) > 100:
            return _error_validacion(
                "Idempotency-Key",
                "La clave no puede superar los 100 caracteres.",
            )

        existente = Orden.objects.filter(idempotency_key=idempotency_key).first()
        if existente:
            if _validar_items(items) or not _coincide_con_orden(
                existente, request.user.id, items
            ):
                return _conflicto_idempotencia()
            return Response(self._serializar_orden(existente), status=status.HTTP_200_OK)

        error = _validar_items(items)
        if error:
            return error

        if total_esperado is not None and (
            type(total_esperado) is not int or total_esperado < 0
        ):
            return _error_validacion(
                "total_esperado",
                "Debe ser un total entero no negativo.",
            )

        try:
            lineas, total, puede_pagar = calcular_lineas(items)
        except CatalogoNoDisponibleError as exc:
            return Response(
                {"error": {"codigo": "catalogo_no_disponible", "mensaje": str(exc)}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except RespuestaCatalogoInvalidaError as exc:
            return Response(
                {"error": {"codigo": "respuesta_catalogo_invalida", "mensaje": str(exc)}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not puede_pagar:
            return Response(
                {"error": {
                    "codigo": "carrito_inconsistente",
                    "mensaje": "Hay productos no disponibles.",
                    "carrito": {"moneda": "CLP", "lineas": lineas, "total": total, "puede_pagar": puede_pagar},
                }},
                status=status.HTTP_409_CONFLICT,
            )

        if total_esperado is not None and int(total_esperado) != int(total):
            return Response(
                {"error": {
                    "codigo": "precio_cambiado",
                    "mensaje": "El total del carrito cambió.",
                    "carrito": {"moneda": "CLP", "lineas": lineas, "total": total, "puede_pagar": puede_pagar},
                }},
                status=status.HTTP_409_CONFLICT,
            )

        orden_id = uuid.uuid4()
        reserva = inventario.OrdenReserva(
            id=orden_id,
            cliente_id=uuid.UUID(str(request.user.id)),
            lineas=tuple(
                inventario.LineaReserva(
                    producto_id=linea["producto_id"],
                    cantidad=linea["cantidad"],
                )
                for linea in lineas
            ),
        )
        try:
            inventario.reservar(reserva)
        except inventario.InventarioNoDisponible:
            return Response(
                {
                    "error": {
                        "codigo": "inventario_no_disponible",
                        "mensaje": "No se pudo apartar el stock; la orden no fue creada.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            with transaction.atomic():
                orden = Orden.objects.create(
                    id=orden_id,
                    cliente_id=request.user.id,
                    estado="PENDIENTE_PAGO",
                    moneda="CLP",
                    total=Decimal(total),
                    idempotency_key=idempotency_key,
                )

                for linea in lineas:
                    DetalleOrden.objects.create(
                        orden=orden,
                        producto_id=linea["producto_id"],
                        nombre_producto=linea["nombre"] or "",
                        precio_unitario=Decimal(linea["precio_unitario"] or 0),
                        cantidad=linea["cantidad"],
                        subtotal=Decimal(linea["subtotal"]),
                    )
        except IntegrityError:
            self._liberar_reserva_no_persistida(reserva)
            existente = Orden.objects.filter(idempotency_key=idempotency_key).first()
            if existente is None:
                raise
            if not _coincide_con_orden(existente, request.user.id, items):
                return _conflicto_idempotencia()
            return Response(self._serializar_orden(existente), status=status.HTTP_200_OK)
        except DatabaseError:
            self._liberar_reserva_no_persistida(reserva)
            raise

        return Response(self._serializar_orden(orden), status=status.HTTP_201_CREATED)

    @staticmethod
    def _liberar_reserva_no_persistida(reserva):
        try:
            inventario.liberar(reserva)
        except Exception as exc:
            log.error(
                "No se pudo liberar reserva sin orden persistida %s: %s",
                reserva.id,
                type(exc).__name__,
            )

    def _serializar_orden(self, orden):
        return {
            "orden": {
                "id": str(orden.id),
                "estado": orden.estado,
                "moneda": orden.moneda,
                "lineas": [
                    {
                        "producto_id": l.producto_id,
                        "nombre": l.nombre_producto,
                        "precio_unitario": int(l.precio_unitario),
                        "cantidad": l.cantidad,
                        "subtotal": int(l.subtotal),
                    }
                    for l in orden.lineas.all()
                ],
                "total": int(orden.total),
                "creada_en": orden.creado_en.isoformat(),
            },
        }
