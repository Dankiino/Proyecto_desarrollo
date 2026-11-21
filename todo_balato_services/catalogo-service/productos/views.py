import math

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .repository import (
    comprobar_lectura,
    listar_productos,
    obtener_producto,
    listar_categorias,
)


def formatear_imagen(imagen):
    """Adapta una imagen de MongoDB al formato que utilizará React."""
    return {
        "url": imagen.get("url", ""),
        "texto_alternativo": imagen.get("alt", ""),
    }


def formatear_producto(producto, detalle=False):
    """Convierte un documento MongoDB en una respuesta pública."""
    imagenes = [
        formatear_imagen(imagen)
        for imagen in producto.get("imagenes", [])
    ]

    stock_fisico = int(producto.get("stock_fisico", 0))
    stock_reservado = int(producto.get("stock_reservado", 0))
    stock_disponible = max(0, stock_fisico - stock_reservado)

    resultado = {
    "id": str(producto["_id"]),
    "nombre": producto.get("nombre", ""),
    "precio": producto.get("precio", 0),
    "moneda": producto.get("moneda", "CLP"),
    "imagen_principal": imagenes[0] if imagenes else None,
    "disponible": stock_disponible > 0,
    "categoria_id": producto.get("categoria_id", ""),
}

    if detalle:
        resultado.update({
            "descripcion": producto.get("descripcion", ""),
            "imagenes": imagenes,
            "stock_fisico": stock_fisico,
            "stock_reservado": stock_reservado,
            "stock_disponible": stock_disponible,
            "categoria_id": producto.get("categoria_id", ""),
        })

    return resultado


class HealthView(APIView):
    def get(self, request):
        return Response({
            "status": "ok",
            "service": "catalogo-service"
        })


class MongoHealthView(APIView):
    def get(self, request):
        colecciones = comprobar_lectura()
        return Response({
            "status": "ok",
            "service": "catalogo-service",
            "mongo": colecciones
        })


class ProductosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            pagina = int(request.query_params.get("page", 1))
            tamano = int(request.query_params.get("limit", 20))
        except (ValueError, TypeError):
            return Response(
                {"error": "Los parámetros page y limit deben ser números enteros."},
                status=400
            )

        if pagina < 1 or tamano < 1:
            return Response(
                {"error": "page y limit deben ser mayores que cero."},
                status=400
            )

        tamano = min(tamano, 50)
        categoria_id = request.query_params.get("categoria_id")

        productos, total = listar_productos(
            categoria_id=categoria_id,
            solo_activos=True,
            pagina=pagina,
            tamano=tamano
        )

        resultados = [
            formatear_producto(producto)
            for producto in productos
        ]

        return Response({
            "resultados": resultados,
            "paginacion": {
                "pagina": pagina,
                "limite": tamano,
                "total": total,
                "total_paginas": math.ceil(total / tamano)
            }
        })


class ProductoDetalleView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, producto_id):
        producto = obtener_producto(
            producto_id,
            solo_activos=True
        )

        if producto is None:
            return Response(
                {"error": "Producto no encontrado."},
                status=404
            )

        return Response(formatear_producto(producto, detalle=True))


class CategoriasView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categorias = listar_categorias(solo_activas=True)

        resultados = [
            {
                "id": str(categoria["_id"]),
                "nombre": categoria.get("nombre", ""),
                "descripcion": categoria.get("descripcion", ""),
                "orden": categoria.get("orden", 0)
            }
            for categoria in categorias
        ]

        return Response({"resultados": resultados})
