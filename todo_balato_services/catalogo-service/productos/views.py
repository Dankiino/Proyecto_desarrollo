from datetime import date, datetime, timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import repository
from .admin_auth import verificar_admin
from .repository import (
    actualizar_categoria,
    actualizar_producto,
    comprobar_lectura,
    crear_categoria,
    crear_producto,
    listar_categorias,
    listar_productos,
    obtener_categoria,
    obtener_producto,
)
from .reservas_repo import (
    ErrorReservaNegocio,
    confirmar_reserva,
    consultar_productos_para_comercio,
    crear_reserva_atomica,
    liberar_reserva,
    obtener_reserva,
)
from .serializers import (
    AjusteInventarioSerializer,
    CategoriaSerializer,
    ProductoCrearSerializer,
)
from .servicio_auth import verificar_credencial_servicio


ORDENES = {"recientes", "precio_asc", "precio_desc", "nombre_asc"}


def _error_validacion(campo, mensaje):
    return Response(
        {
            "error": {
                "codigo": "validacion",
                "mensaje": "Los datos enviados no son válidos.",
                "campos": {campo: [mensaje]},
            }
        },
        status=400,
    )


def _entero_parametro(request, nombre, defecto=None, minimo=None, maximo=None):
    valor = request.query_params.get(nombre)
    if valor is None:
        return defecto, None
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None, _error_validacion(nombre, "Debe ser un número entero.")
    if (minimo is not None and numero < minimo) or (
        maximo is not None and numero > maximo
    ):
        if nombre == "page_size":
            mensaje = "Debe ser un entero entre 1 y 50."
        elif nombre == "page":
            mensaje = "Debe ser un entero mayor o igual a 1."
        else:
            mensaje = "Debe ser un entero no negativo."
        return None, _error_validacion(nombre, mensaje)
    return numero, None


def _fecha_iso(valor):
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def _categorias_producto(producto, nombres_categoria):
    asignadas = producto.get("categorias")
    if asignadas is None:
        asignadas = producto.get("categoria_ids")
    if asignadas is None and producto.get("categoria_id") is not None:
        asignadas = [producto["categoria_id"]]
    if not isinstance(asignadas, list):
        asignadas = [asignadas] if asignadas is not None else []

    resultado = []
    for categoria in asignadas:
        if isinstance(categoria, dict):
            categoria_id = categoria.get("id", categoria.get("_id"))
            nombre = categoria.get("nombre")
        else:
            categoria_id = categoria
            nombre = None
        if categoria_id is None:
            continue
        categoria_id = str(categoria_id)
        resultado.append(
            {
                "id": categoria_id,
                "nombre": nombre or nombres_categoria.get(categoria_id, categoria_id),
            }
        )
    return resultado


def _imagen_publica(imagen):
    return {
        "url": imagen.get("url"),
        "texto_alternativo": imagen.get(
            "texto_alternativo", imagen.get("alt", "")
        ),
    }


def _producto_publico(producto, nombres_categoria, detalle=False):
    imagenes = [
        _imagen_publica(imagen)
        for imagen in (producto.get("imagenes") or [])
        if isinstance(imagen, dict)
    ]
    stock_fisico = int(producto.get("stock_fisico", 0) or 0)
    stock_reservado = int(producto.get("stock_reservado", 0) or 0)
    stock_disponible = max(stock_fisico - stock_reservado, 0)
    resultado = {
        "id": str(producto.get("_id", producto.get("id", ""))),
        "nombre": producto.get("nombre", ""),
        "imagen_principal": imagenes[0] if imagenes else None,
        "precio": producto.get("precio", 0),
        "moneda": producto.get("moneda", "CLP"),
        "disponible": stock_disponible > 0,
        "categorias": _categorias_producto(producto, nombres_categoria),
    }
    if detalle:
        resultado.update(
            {
                "descripcion": producto.get("descripcion", ""),
                "stock_disponible": stock_disponible,
                "imagenes": imagenes,
                "actualizado_en": _fecha_iso(producto.get("actualizado_en")),
            }
        )
    return resultado


def _mapa_categorias():
    return {
        str(categoria.get("_id", categoria.get("id"))): categoria.get(
            "nombre", str(categoria.get("_id", categoria.get("id")))
        )
        for categoria in repository.listar_categorias()
    }


def _validar_items_payload(data):
    if not isinstance(data, dict):
        return None, _error_validacion("items", "Debe enviarse un objeto JSON válido.")

    items = data.get("items")
    if not isinstance(items, list) or len(items) == 0:
        return None, _error_validacion("items", "Debe ser una lista no vacía.")

    validados = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            return None, _error_validacion(f"items[{idx}]", "Cada ítem debe ser un objeto.")

        pid = item.get("producto_id")
        if not isinstance(pid, str) or not pid.strip():
            return None, _error_validacion(
                f"items[{idx}].producto_id", "Debe ser un identificador de texto no vacío."
            )

        cantidad = item.get("cantidad")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            return None, _error_validacion(
                f"items[{idx}].cantidad", "Debe ser un número entero mayor a 0."
            )

        validados.append({"producto_id": pid.strip(), "cantidad": cantidad})

    return validados, None


def _serializar_reserva(reserva):
    return {
        "reserva_id": str(reserva.get("_id", "")),
        "orden_id": reserva.get("orden_id", ""),
        "estado": reserva.get("estado", ""),
        "items": reserva.get("items", []),
        "creado_en": _fecha_iso(reserva.get("creado_en")),
        "actualizado_en": _fecha_iso(reserva.get("actualizado_en")),
        "confirmada_en": _fecha_iso(reserva.get("confirmada_en"))
        if reserva.get("confirmada_en")
        else None,
        "liberada_en": _fecha_iso(reserva.get("liberada_en"))
        if reserva.get("liberada_en")
        else None,
    }


def _respuesta_error_reserva(exc):
    return Response(
        {
            "error": {
                "codigo": exc.codigo,
                "mensaje": exc.mensaje,
                "detalles": exc.detalles,
            }
        },
        status=exc.status_code,
    )


class CategoriasView(APIView):
    def get(self, request):
        categorias = [
            {
                "id": str(categoria.get("_id", categoria.get("id", ""))),
                "nombre": categoria.get("nombre", ""),
            }
            for categoria in repository.listar_categorias()
        ]
        return Response({"results": categorias})


class ProductosView(APIView):
    def get(self, request):
        page, error = _entero_parametro(request, "page", 1, minimo=1)
        if error:
            return error
        page_size, error = _entero_parametro(
            request, "page_size", 20, minimo=1, maximo=50
        )
        if error:
            return error
        precio_min, error = _entero_parametro(request, "precio_min", minimo=0)
        if error:
            return error
        precio_max, error = _entero_parametro(request, "precio_max", minimo=0)
        if error:
            return error
        if precio_min is not None and precio_max is not None and precio_min > precio_max:
            return _error_validacion(
                "precio_max", "No puede ser menor que precio_min."
            )

        orden = request.query_params.get("orden", "recientes")
        if orden not in ORDENES:
            return _error_validacion("orden", "El valor de orden no es válido.")

        disponible = request.query_params.get("disponible")
        if disponible not in (None, "true"):
            return _error_validacion("disponible", "El único valor permitido es true.")

        productos, total = repository.listar_productos(
            categoria_id=request.query_params.get("categoria") or None,
            precio_min=precio_min,
            precio_max=precio_max,
            disponible=disponible == "true",
            pagina=page,
            tamano=page_size,
            orden=orden,
            buscar=request.query_params.get("buscar", ""),
        )
        nombres_categoria = _mapa_categorias()
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": [
                    _producto_publico(producto, nombres_categoria)
                    for producto in productos
                ],
            }
        )


class ProductoDetalleView(APIView):
    def get(self, request, producto_id):
        producto = repository.obtener_producto(producto_id)
        if producto is None:
            return Response(
                {
                    "error": {
                        "codigo": "no_encontrado",
                        "mensaje": "El producto no existe o no está disponible.",
                    }
                },
                status=404,
            )
        return Response(
            _producto_publico(producto, _mapa_categorias(), detalle=True)
        )


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
            "categoria_id",
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

        actualizado = actualizar_producto(producto_id, cambios)

        return Response({
            "mensaje": "Producto actualizado correctamente",
            "producto": actualizado
        })


class AdminAjustesInventarioView(APIView):

    def get(self, request, producto_id):
        verificar_admin(request)

        producto = repository.obtener_producto(
            producto_id,
            solo_activos=False
        )

        if producto is None:
            return Response(
                {"error": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        historial = producto.get("historial_ajustes", [])

        return Response({
            "producto_id": producto_id,
            "stock_fisico": producto["stock_fisico"],
            "stock_reservado": producto.get("stock_reservado", 0),
            "total": len(historial),
            "historial": list(reversed(historial))
        })

    def post(self, request, producto_id):
        administrador = verificar_admin(request)

        serializer = AjusteInventarioSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        actualizado = repository.ajustar_inventario(
            producto_id=producto_id,
            stock_nuevo=datos["stock_fisico"],
            motivo=datos["motivo"],
            administrador=administrador
        )

        if actualizado is None:
            producto = repository.obtener_producto(
                producto_id,
                solo_activos=False
            )

            if producto is None:
                return Response(
                    {"error": "Producto no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "error": "El ajuste no cumple las condiciones del inventario.",
                    "stock_reservado": producto.get("stock_reservado", 0)
                },
                status=status.HTTP_409_CONFLICT
            )

        return Response(
            {
                "mensaje": "Ajuste de inventario registrado correctamente.",
                "stock_fisico": actualizado["stock_fisico"],
                "stock_reservado": actualizado["stock_reservado"],
                "ajuste": actualizado["historial_ajustes"][-1]
            },
            status=status.HTTP_201_CREATED
        )


class InternoProductosConsultaView(APIView):
    def post(self, request):
        verificar_credencial_servicio(request)
        items, error = _validar_items_payload(request.data)
        if error:
            return error
        try:
            productos = consultar_productos_para_comercio(items)
        except ErrorReservaNegocio as exc:
            return _respuesta_error_reserva(exc)
        return Response({"results": productos}, status=status.HTTP_200_OK)


class InternoReservasView(APIView):
    def post(self, request):
        verificar_credencial_servicio(request)
        if not isinstance(request.data, dict):
            return _error_validacion("orden_id", "Debe enviarse un objeto JSON válido.")

        orden_id = request.data.get("orden_id")
        if not isinstance(orden_id, str) or not orden_id.strip():
            return _error_validacion("orden_id", "Debe ser un identificador de texto no vacío.")

        items, error = _validar_items_payload(request.data)
        if error:
            return error

        try:
            reserva, creada = crear_reserva_atomica(orden_id.strip(), items)
        except ErrorReservaNegocio as exc:
            return _respuesta_error_reserva(exc)

        codigo_http = status.HTTP_201_CREATED if creada else status.HTTP_200_OK
        return Response(_serializar_reserva(reserva), status=codigo_http)


class InternoReservaDetalleView(APIView):
    def get(self, request, orden_id):
        verificar_credencial_servicio(request)
        reserva = obtener_reserva(orden_id)
        if reserva is None:
            return Response(
                {
                    "error": {
                        "codigo": "reserva_no_encontrada",
                        "mensaje": "No existe una reserva asociada a la orden indicada.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_serializar_reserva(reserva), status=status.HTTP_200_OK)


class InternoReservaConfirmarView(APIView):
    def post(self, request, orden_id):
        verificar_credencial_servicio(request)
        try:
            reserva = confirmar_reserva(orden_id)
        except ErrorReservaNegocio as exc:
            return _respuesta_error_reserva(exc)
        return Response(_serializar_reserva(reserva), status=status.HTTP_200_OK)


class InternoReservaLiberarView(APIView):
    def post(self, request, orden_id):
        verificar_credencial_servicio(request)
        try:
            reserva = liberar_reserva(orden_id)
        except ErrorReservaNegocio as exc:
            return _respuesta_error_reserva(exc)
        return Response(_serializar_reserva(reserva), status=status.HTTP_200_OK)