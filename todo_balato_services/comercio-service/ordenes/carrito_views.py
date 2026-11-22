from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalogo_client import CatalogoNoDisponibleError, RespuestaCatalogoInvalidaError
from .models import Carrito, LineaCarrito
from .permissions import EsClienteActivo
from .views import calcular_lineas

CANTIDAD_MAXIMA = 99


def _error(codigo, mensaje, http_status):
    return Response(
        {"error": {"codigo": codigo, "mensaje": mensaje}},
        status=http_status,
    )


def _datos(request):
    return request.data if isinstance(request.data, dict) else {}


def _cantidad_valida(valor):
    """Devuelve la cantidad si es un entero entre 0 y el máximo; si no, None."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None
    if valor < 0 or valor > CANTIDAD_MAXIMA:
        return None
    return valor


def _producto_id_valido(valor):
    return isinstance(valor, str) and 0 < len(valor) <= 100


def _items(carrito):
    """Solo identificador y cantidad: eso es lo único que se guarda."""
    return [
        {"producto_id": linea.producto_id, "cantidad": linea.cantidad}
        for linea in carrito.lineas.order_by("producto_id")
    ]


class CarritoView(APIView):
    permission_classes = [EsClienteActivo]

    def get(self, request):
        carrito = Carrito.objects.filter(cliente_id=request.user.id).first()
        items = _items(carrito) if carrito else []

        if not items:
            return Response({
                "items": [], "moneda": "CLP", "lineas": [],
                "total": 0, "puede_pagar": False, "avisos": [],
            })

        # Precio y stock se vuelven a consultar siempre en Catálogo.
        try:
            lineas, total, puede_pagar = calcular_lineas(items)
        except CatalogoNoDisponibleError as exc:
            return _error("catalogo_no_disponible", str(exc),
                          status.HTTP_503_SERVICE_UNAVAILABLE)
        except RespuestaCatalogoInvalidaError as exc:
            return _error("respuesta_catalogo_invalida", str(exc),
                          status.HTTP_502_BAD_GATEWAY)

        avisos = [
            {"producto_id": l["producto_id"], "problema": l["problema"]}
            for l in lineas if l["problema"]
        ]
        return Response({
            "items": items, "moneda": "CLP", "lineas": lineas,
            "total": total, "puede_pagar": puede_pagar, "avisos": avisos,
        })


class ItemCarritoView(APIView):
    permission_classes = [EsClienteActivo]

    def put(self, request, producto_id):
        if not _producto_id_valido(producto_id):
            return _error("validacion", "Identificador de producto inválido.",
                          status.HTTP_400_BAD_REQUEST)

        cantidad = _cantidad_valida(_datos(request).get("cantidad"))
        if cantidad is None:
            return _error(
                "validacion",
                f"La cantidad debe ser un entero entre 0 y {CANTIDAD_MAXIMA}.",
                status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            carrito, _ = Carrito.objects.get_or_create(cliente_id=request.user.id)
            if cantidad == 0:
                LineaCarrito.objects.filter(
                    carrito=carrito, producto_id=producto_id
                ).delete()
            else:
                LineaCarrito.objects.update_or_create(
                    carrito=carrito,
                    producto_id=producto_id,
                    defaults={"cantidad": cantidad},
                )
        return Response({"items": _items(carrito)})

    def delete(self, request, producto_id):
        carrito = Carrito.objects.filter(cliente_id=request.user.id).first()
        if carrito:
            LineaCarrito.objects.filter(
                carrito=carrito, producto_id=producto_id
            ).delete()
        return Response({"items": _items(carrito) if carrito else []})


class CombinarCarritoView(APIView):
    """Mezcla el carrito anónimo con el guardado. Regla: gana la mayor cantidad."""

    permission_classes = [EsClienteActivo]

    def post(self, request):
        items = _datos(request).get("items")
        if not isinstance(items, list):
            return _error("validacion", "Se esperaba una lista de items.",
                          status.HTTP_400_BAD_REQUEST)

        anonimo = {}
        for item in items:
            if not isinstance(item, dict):
                return _error("validacion", "Cada item debe ser un objeto.",
                              status.HTTP_400_BAD_REQUEST)
            producto_id = item.get("producto_id")
            cantidad = _cantidad_valida(item.get("cantidad"))
            if not _producto_id_valido(producto_id) or not cantidad:
                return _error(
                    "validacion",
                    "Cada item necesita producto_id y una cantidad válida mayor que 0.",
                    status.HTTP_400_BAD_REQUEST,
                )
            # Repetidos dentro del mismo carrito anónimo: también la mayor.
            anonimo[producto_id] = max(anonimo.get(producto_id, 0), cantidad)

        with transaction.atomic():
            carrito, _ = Carrito.objects.get_or_create(cliente_id=request.user.id)
            for producto_id, cantidad in anonimo.items():
                linea = LineaCarrito.objects.filter(
                    carrito=carrito, producto_id=producto_id
                ).first()
                if linea is None:
                    LineaCarrito.objects.create(
                        carrito=carrito, producto_id=producto_id, cantidad=cantidad
                    )
                elif cantidad > linea.cantidad:
                    linea.cantidad = cantidad
                    linea.save(update_fields=["cantidad"])

        return Response({"items": _items(carrito)})