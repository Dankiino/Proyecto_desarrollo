from datetime import datetime, timezone
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from .mongo import errores_mongo, get_productos, get_reservas


class ErrorReservaNegocio(Exception):
    def __init__(self, codigo, mensaje, status_code=400, detalles=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.status_code = status_code
        self.detalles = detalles or {}


def asegurar_indice_reservas():
    with errores_mongo():
        get_reservas().create_index(
            [("orden_id", ASCENDING)],
            unique=True,
            name="orden_id_unique",
        )


def _normalizar_items(items):
    agrupado = {}
    for item in items:
        pid = item["producto_id"]
        cant = item["cantidad"]
        agrupado[pid] = agrupado.get(pid, 0) + cant
    return [
        {"producto_id": pid, "cantidad": cant}
        for pid, cant in sorted(agrupado.items())
    ]


def consultar_productos_para_comercio(items):
    normalizados = _normalizar_items(items)
    resultado = []
    with errores_mongo():
        col_prod = get_productos()
        for linea in normalizados:
            pid = linea["producto_id"]
            cant = linea["cantidad"]
            prod = col_prod.find_one({"_id": pid, "activo": True})
            if prod is None:
                raise ErrorReservaNegocio(
                    codigo="producto_no_disponible",
                    mensaje=f"El producto '{pid}' no existe o está inactivo.",
                    status_code=404,
                    detalles={"producto_id": pid},
                )
            stock_fisico = int(prod.get("stock_fisico", 0) or 0)
            stock_reservado = int(prod.get("stock_reservado", 0) or 0)
            stock_disponible = max(stock_fisico - stock_reservado, 0)
            resultado.append(
                {
                    "producto_id": pid,
                    "nombre": prod.get("nombre", ""),
                    "precio": prod.get("precio", 0),
                    "moneda": prod.get("moneda", "CLP"),
                    "stock_fisico": stock_fisico,
                    "stock_reservado": stock_reservado,
                    "stock_disponible": stock_disponible,
                    "cantidad_solicitada": cant,
                    "stock_suficiente": stock_disponible >= cant,
                }
            )
    return resultado


def _revertir_reservas_parciales(col_prod, aplicadas):
    for linea in reversed(aplicadas):
        pid = linea["producto_id"]
        cant = linea["cantidad"]
        col_prod.find_one_and_update(
            {"_id": pid, "stock_reservado": {"$gte": cant}},
            {"$inc": {"stock_reservado": -cant, "version": -1}},
        )


def crear_reserva_atomica(orden_id, items):
    normalizados = _normalizar_items(items)
    ahora = datetime.now(timezone.utc)

    with errores_mongo():
        col_reservas = get_reservas()
        col_prod = get_productos()

        existente = col_reservas.find_one({"orden_id": orden_id})
        if existente is not None:
            if _normalizar_items(existente.get("items", [])) == normalizados:
                return existente, False
            raise ErrorReservaNegocio(
                codigo="conflicto_orden_id",
                mensaje="Ya existe una reserva con este orden_id y distintos ítems.",
                status_code=409,
                detalles={"orden_id": orden_id},
            )

        for linea in normalizados:
            pid = linea["producto_id"]
            prod = col_prod.find_one({"_id": pid, "activo": True})
            if prod is None:
                raise ErrorReservaNegocio(
                    codigo="producto_no_disponible",
                    mensaje=f"El producto '{pid}' no existe o está inactivo.",
                    status_code=404,
                    detalles={"producto_id": pid},
                )

        aplicadas = []
        lineas_reservadas = []

        for linea in normalizados:
            pid = linea["producto_id"]
            cant = linea["cantidad"]
            actualizado = col_prod.find_one_and_update(
                {
                    "_id": pid,
                    "activo": True,
                    "$expr": {
                        "$gte": [
                            {
                                "$subtract": [
                                    {"$ifNull": ["$stock_fisico", 0]},
                                    {"$ifNull": ["$stock_reservado", 0]},
                                ]
                            },
                            cant,
                        ]
                    },
                },
                {
                    "$inc": {"stock_reservado": cant, "version": 1},
                    "$set": {"actualizado_en": ahora},
                },
                return_document=ReturnDocument.AFTER,
            )
            if actualizado is None:
                _revertir_reservas_parciales(col_prod, aplicadas)
                raise ErrorReservaNegocio(
                    codigo="stock_insuficiente",
                    mensaje=f"Stock insuficiente para apartar {cant} unidad(es) del producto '{pid}'. Ninguna línea fue reservada.",
                    status_code=409,
                    detalles={"producto_id": pid, "cantidad_solicitada": cant},
                )

            aplicadas.append(linea)
            lineas_reservadas.append(
                {
                    "producto_id": pid,
                    "cantidad": cant,
                    "precio_unitario": actualizado.get("precio", 0),
                    "moneda": actualizado.get("moneda", "CLP"),
                }
            )

        documento_reserva = {
            "_id": f"res_{orden_id}",
            "orden_id": orden_id,
            "estado": "RESERVADA",
            "items": lineas_reservadas,
            "creado_en": ahora,
            "actualizado_en": ahora,
        }

        try:
            col_reservas.insert_one(documento_reserva)
        except DuplicateKeyError:
            _revertir_reservas_parciales(col_prod, aplicadas)
            existente_concurrente = col_reservas.find_one({"orden_id": orden_id})
            if existente_concurrente and _normalizar_items(existente_concurrente.get("items", [])) == normalizados:
                return existente_concurrente, False
            raise ErrorReservaNegocio(
                codigo="conflicto_orden_id",
                mensaje="Ya existe una reserva registrada para este orden_id.",
                status_code=409,
                detalles={"orden_id": orden_id},
            )

        return documento_reserva, True


def obtener_reserva(orden_id):
    with errores_mongo():
        return get_reservas().find_one({"orden_id": orden_id})


def confirmar_reserva(orden_id):
    ahora = datetime.now(timezone.utc)
    with errores_mongo():
        col_reservas = get_reservas()
        col_prod = get_productos()

        reserva = col_reservas.find_one({"orden_id": orden_id})
        if reserva is None:
            raise ErrorReservaNegocio(
                codigo="reserva_no_encontrada",
                mensaje="No existe una reserva asociada a la orden indicada.",
                status_code=404,
            )

        estado_actual = reserva.get("estado")
        if estado_actual == "CONFIRMADA":
            return reserva
        if estado_actual != "RESERVADA":
            raise ErrorReservaNegocio(
                codigo="transicion_invalida",
                mensaje=f"No se puede confirmar una reserva en estado '{estado_actual}'.",
                status_code=409,
            )

        descontados = []
        for linea in reserva.get("items", []):
            pid = linea["producto_id"]
            cant = int(linea["cantidad"])
            prod_actualizado = col_prod.find_one_and_update(
                {
                    "_id": pid,
                    "stock_fisico": {"$gte": cant},
                    "stock_reservado": {"$gte": cant},
                },
                {
                    "$inc": {
                        "stock_fisico": -cant,
                        "stock_reservado": -cant,
                        "version": 1,
                    },
                    "$set": {"actualizado_en": ahora},
                },
                return_document=ReturnDocument.AFTER,
            )
            if prod_actualizado is None:
                for prev in reversed(descontados):
                    col_prod.find_one_and_update(
                        {"_id": prev["producto_id"]},
                        {
                            "$inc": {
                                "stock_fisico": prev["cantidad"],
                                "stock_reservado": prev["cantidad"],
                                "version": -1,
                            }
                        },
                    )
                raise ErrorReservaNegocio(
                    codigo="inconsistencia_inventario",
                    mensaje=f"No fue posible confirmar el descuento del producto '{pid}'.",
                    status_code=409,
                )
            descontados.append({"producto_id": pid, "cantidad": cant})

        confirmada = col_reservas.find_one_and_update(
            {"orden_id": orden_id, "estado": "RESERVADA"},
            {"$set": {"estado": "CONFIRMADA", "confirmada_en": ahora, "actualizado_en": ahora}},
            return_document=ReturnDocument.AFTER,
        )
        if confirmada is None:
            actual = col_reservas.find_one({"orden_id": orden_id})
            if actual and actual.get("estado") == "CONFIRMADA":
                return actual
            raise ErrorReservaNegocio(
                codigo="transicion_invalida",
                mensaje="El estado de la reserva cambió durante la confirmación.",
                status_code=409,
            )
        return confirmada


def liberar_reserva(orden_id):
    ahora = datetime.now(timezone.utc)
    with errores_mongo():
        col_reservas = get_reservas()
        col_prod = get_productos()

        reserva = col_reservas.find_one({"orden_id": orden_id})
        if reserva is None:
            raise ErrorReservaNegocio(
                codigo="reserva_no_encontrada",
                mensaje="No existe una reserva asociada a la orden indicada.",
                status_code=404,
            )

        estado_actual = reserva.get("estado")
        if estado_actual == "LIBERADA":
            return reserva
        if estado_actual != "RESERVADA":
            raise ErrorReservaNegocio(
                codigo="transicion_invalida",
                mensaje=f"No se puede liberar una reserva en estado '{estado_actual}'.",
                status_code=409,
            )

        for linea in reserva.get("items", []):
            pid = linea["producto_id"]
            cant = int(linea["cantidad"])
            col_prod.find_one_and_update(
                {"_id": pid, "stock_reservado": {"$gte": cant}},
                {
                    "$inc": {"stock_reservado": -cant, "version": 1},
                    "$set": {"actualizado_en": ahora},
                },
                return_document=ReturnDocument.AFTER,
            )

        liberada = col_reservas.find_one_and_update(
            {"orden_id": orden_id, "estado": "RESERVADA"},
            {"$set": {"estado": "LIBERADA", "liberada_en": ahora, "actualizado_en": ahora}},
            return_document=ReturnDocument.AFTER,
        )
        if liberada is None:
            actual = col_reservas.find_one({"orden_id": orden_id})
            if actual and actual.get("estado") == "LIBERADA":
                return actual
            raise ErrorReservaNegocio(
                codigo="transicion_invalida",
                mensaje="El estado de la reserva cambió durante la liberación.",
                status_code=409,
            )
        return liberada
