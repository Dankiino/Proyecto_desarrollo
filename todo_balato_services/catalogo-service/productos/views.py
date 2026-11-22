from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .admin_auth import verificar_admin

from .repository import (
    comprobar_lectura,
    listar_categorias,
    listar_productos,
    crear_producto,
    obtener_producto,
    actualizar_producto,
    crear_categoria,
    obtener_categoria,
    actualizar_categoria,
)

from .serializers import ProductoCrearSerializer, CategoriaSerializer

class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "catalogo-service"})


class MongoHealthView(APIView):
    def get(self, request):
        colecciones = comprobar_lectura()  # lanza CatalogoDBError -> 503
        return Response(
            {"status": "ok", "service": "catalogo-service", "mongo": colecciones}
        )


class AdminVerificarView(APIView):
    def get(self, request):
        usuario = verificar_admin(request)

        return Response({
            "autorizado": True,
            "mensaje": "Acceso administrativo autorizado",
            "correo": usuario["correo"],
        })


class AdminProductosView(APIView):
    def get(self, request):
        verificar_admin(request)

        productos, total = listar_productos(
            solo_activos=False,
            pagina=1,
            tamano=100
        )

        resultado = []

        for producto in productos:
            producto["_id"] = str(producto["_id"])
            resultado.append(producto)

        return Response({
            "total": total,
            "productos": resultado
        })

    def post(self, request):
        verificar_admin(request)

        serializer = ProductoCrearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        producto = crear_producto(serializer.validated_data)

        producto["_id"] = str(producto["_id"])

        return Response(
            {
                "mensaje": "Producto creado correctamente",
                "producto": producto
            },
            status=status.HTTP_201_CREATED
        )




class AdminCategoriasView(APIView):
    def get(self, request):
        verificar_admin(request)

        categorias = listar_categorias(solo_activas=False)

        resultado = []
        for categoria in categorias:
            categoria["_id"] = str(categoria["_id"])
            resultado.append(categoria)

        return Response({
            "total": len(resultado),
            "categorias": resultado
        })

    def post(self, request):
        verificar_admin(request)

        serializer = CategoriaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"campos": serializer.errors},
                status=400
            )

        datos = serializer.validated_data

        if not datos.get("identificador"):
            return Response(
                {"campos": {
                    "identificador": ["Este campo es obligatorio."]
                }},
                status=400
            )

        if obtener_categoria(
            datos["identificador"],
            solo_activas=False
        ):
            return Response(
                {"campos": {
                    "identificador": ["Esta categoría ya existe."]
                }},
                status=400
            )

        categoria = crear_categoria(datos)

        return Response(categoria, status=201)



class AdminCategoriaDetalleView(APIView):
    def patch(self, request, categoria_id):
        verificar_admin(request)

        categoria = obtener_categoria(
            categoria_id,
            solo_activas=False
        )

        if categoria is None:
            return Response(
                {"detail": "Categoría no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        campos_permitidos = {
            "nombre",
            "descripcion",
            "orden",
            "activa",
        }

        campos_recibidos = set(request.data.keys())

        if not campos_recibidos or not campos_recibidos.issubset(campos_permitidos):
            return Response(
                {"campos": {
                    "general": ["Solo puedes editar nombre, descripción, orden y activa."]
                }},
                status=status.HTTP_400_BAD_REQUEST
            )

        datos = {
            "nombre": categoria["nombre"],
            "descripcion": categoria.get("descripcion", ""),
            "orden": categoria["orden"],
            "activa": categoria["activa"],
        }

        datos.update(request.data)

        serializer = CategoriaSerializer(data=datos)

        if not serializer.is_valid():
            return Response(
                {"campos": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        cambios = {
            campo: serializer.validated_data[campo]
            for campo in campos_recibidos
        }

        actualizada = actualizar_categoria(categoria_id, cambios)

        if actualizada is None:
            return Response(
                {"detail": "Categoría no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "mensaje": "Categoría actualizada correctamente.",
            "categoria": actualizada
        })


class AdminProductoDetalleView(APIView):
    def get(self, request, producto_id):
        verificar_admin(request)

        producto = obtener_producto(
            producto_id,
            solo_activos=False
        )

        if producto is None:
            return Response(
                {"error": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        producto["_id"] = str(producto["_id"])

        return Response({
            "producto": producto
        })

    def patch(self, request, producto_id):
        verificar_admin(request)

        producto = obtener_producto(
            producto_id,
            solo_activos=False
        )

        if producto is None:
            return Response(
                {"error": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        campos_editables = {
            "nombre",
            "descripcion",
            "precio",
            "stock_fisico",
            "categoria_id",
            "imagenes",
            "activo",
        }

        campos_recibidos = set(request.data.keys())

        if not campos_recibidos or not campos_recibidos.issubset(campos_editables):
            return Response(
                {"error": "No se enviaron campos editables válidos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        datos_completos = {
            "nombre": producto["nombre"],
            "descripcion": producto["descripcion"],
            "precio": producto["precio"],
            "stock_fisico": producto["stock_fisico"],
            "categoria_id": producto["categoria_id"],
            "imagenes": producto["imagenes"],
        }
        datos_completos.update({
            campo: request.data[campo]
            for campo in campos_recibidos
            if campo != "activo"
        })


        if "activo" in request.data:
            if not isinstance(request.data["activo"], bool):
                return Response(
                    {"error": "El campo activo debe ser true o false"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = ProductoCrearSerializer(data=datos_completos)
        serializer.is_valid(raise_exception=True)

        cambios = {
            campo: serializer.validated_data[campo]
            for campo in campos_recibidos
            if campo != "activo"
        }

        if "activo" in campos_recibidos:
            cambios["activo"] = request.data["activo"]

        stock_reservado = producto.get("stock_reservado", 0)

        if (
            "stock_fisico" in cambios
            and cambios["stock_fisico"] < stock_reservado
        ):
            return Response(
                {"error": "El stock físico no puede ser menor al stock reservado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        actualizado = actualizar_producto(producto_id, cambios)

        return Response({
            "mensaje": "Producto actualizado correctamente",
            "producto": actualizado
        })




class ProductosPublicosView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        categoria = request.query_params.get("categoria")
        buscar = request.query_params.get("buscar", "").strip()

        try:
            pagina = int(request.query_params.get("pagina", 1))
            tamano = int(request.query_params.get("tamano", 20))
        except (ValueError, TypeError):
            return Response(
                {"error": "La página y el tamaño deben ser números enteros"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pagina < 1 or tamano < 1 or tamano > 100:
            return Response(
                {"error": "La página debe ser mayor a 0 y el tamaño debe estar entre 1 y 100"},
                status=status.HTTP_400_BAD_REQUEST
            )


        productos, total = listar_productos(
            categoria_id=categoria,
            solo_activos=True,
            pagina=pagina,
            tamano=tamano,
            buscar=buscar
        )


        resultado = []

        for producto in productos:
            producto["_id"] = str(producto["_id"])
            resultado.append(producto)

        total_paginas = (total + tamano - 1) // tamano

        return Response({
            "total": total,
            "pagina": pagina,
            "tamano": tamano,
            "total_paginas": total_paginas,
            "categoria": categoria,
            "buscar": buscar,
            "productos": resultado
        })
