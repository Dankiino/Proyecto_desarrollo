import uuid
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .catalogo_client import obtener_producto
from .models import Orden, DetalleOrden
from .permissions import EsClienteActivo


def calcular_lineas(items):
    lineas = []
    total = 0
    puede_pagar = True

    for item in items:
        producto_id = item.get("producto_id")
        cantidad = item.get("cantidad", 0)
        producto = obtener_producto(producto_id)

        if not producto:
            lineas.append({
                "producto_id": producto_id, "nombre": None, "precio_unitario": None,
                "cantidad": cantidad, "subtotal": 0, "problema": "no_existe",
            })
            puede_pagar = False
            continue

        stock_disponible = producto.get("stock_fisico", 0) - producto.get("stock_reservado", 0)
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
        if not items:
            return Response(
                {"error": {"codigo": "validacion", "mensaje": "El carrito está vacío."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lineas, total, puede_pagar = calcular_lineas(items)

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

        existente = Orden.objects.filter(idempotency_key=idempotency_key).first()
        if existente:
            return Response(self._serializar_orden(existente), status=status.HTTP_200_OK)

        if not items:
            return Response(
                {"error": {"codigo": "validacion", "mensaje": "El carrito está vacío."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lineas, total, puede_pagar = calcular_lineas(items)

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

        orden = Orden.objects.create(
            id=uuid.uuid4(),
            cliente_id=request.user.id,
            estado="PENDIENTE_PAGO",
            moneda="CLP",
            total=Decimal(total),
            idempotency_key=idempotency_key,
        )

        for l in lineas:
            DetalleOrden.objects.create(
                orden=orden,
                producto_id=l["producto_id"],
                nombre_producto=l["nombre"] or "",
                precio_unitario=Decimal(l["precio_unitario"] or 0),
                cantidad=l["cantidad"],
                subtotal=Decimal(l["subtotal"]),
            )

        # TODO: reservar stock vía endpoint interno de Catálogo (pendiente)
        # TODO: crear transacción real en Webpay sandbox (pendiente)

        return Response(self._serializar_orden(orden), status=status.HTTP_201_CREATED)

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