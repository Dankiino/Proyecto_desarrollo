
from datetime import datetime, timezone
from uuid import uuid4
from pymongo import ReturnDocument
import re

from .mongo import (
    COLECCION_CATEGORIAS,
    COLECCION_PRODUCTOS,
    ColeccionSinDatos,
    errores_mongo,
    get_categorias,
    get_db,
    get_productos,
)


def listar_categorias(solo_activas=True):
    filtro = {"activa": True} if solo_activas else {}

    with errores_mongo():
        return list(
            get_categorias().find(filtro).sort("orden", 1)
        )


def obtener_categoria(slug, solo_activas=True):
    filtro = {"_id": slug}

    if solo_activas:
        filtro["activa"] = True

    with errores_mongo():
        return get_categorias().find_one(filtro)


def listar_productos(
    categoria_id=None,
    precio_min=None,
    precio_max=None,
    disponible=None,
    solo_activos=True,
    pagina=1,
    tamano=20,
    orden="recientes",
    buscar=None,
):
    filtro = {}
    condiciones = []

    if solo_activos:
        filtro["activo"] = True

    if categoria_id:
        condiciones.append({
            "$or": [
                {"categoria_id": categoria_id},
                {"categoria_ids": categoria_id},
                {"categorias.id": categoria_id},
                {"categorias": categoria_id},
            ]
        })

    if buscar and buscar.strip():
        texto = re.escape(buscar.strip())

        condiciones.append({
            "$or": [
                {
                    "nombre": {
                        "$regex": texto,
                        "$options": "i",
                    }
                },
                {
                    "descripcion": {
                        "$regex": texto,
                        "$options": "i",
                    }
                },
            ]
        })

    if condiciones:
        filtro["$and"] = condiciones

    if precio_min is not None or precio_max is not None:
        filtro["precio"] = {}

        if precio_min is not None:
            filtro["precio"]["$gte"] = precio_min

        if precio_max is not None:
            filtro["precio"]["$lte"] = precio_max

    if disponible is True:
        filtro["$expr"] = {
            "$gt": [
                {
                    "$subtract": [
                        {"$ifNull": ["$stock_fisico", 0]},
                        {"$ifNull": ["$stock_reservado", 0]},
                    ]
                },
                0,
            ]
        }

    ordenes = {
        "recientes": [
            ("actualizado_en", -1),
            ("_id", -1),
        ],
        "precio_asc": [
            ("precio", 1),
            ("_id", 1),
        ],
        "precio_desc": [
            ("precio", -1),
            ("_id", -1),
        ],
        "nombre_asc": [
            ("nombre", 1),
            ("_id", 1),
        ],
    }

    with errores_mongo():
        col = get_productos()

        total = col.count_documents(filtro)

        items = list(
            col.find(filtro)
            .sort(ordenes[orden])
            .skip((pagina - 1) * tamano)
            .limit(tamano)
        )

    return items, total


def obtener_producto(producto_id, solo_activos=True):
    filtro = {"_id": producto_id}

    if solo_activos:
        filtro["activo"] = True

    with errores_mongo():
        return get_productos().find_one(filtro)


def comprobar_lectura():
    """Verifica conexión y lectura de ambas colecciones. Devuelve solo conteos."""

    resultado = {}

    with errores_mongo():
        db = get_db()
        db.command("ping")

        for nombre in (
            COLECCION_PRODUCTOS,
            COLECCION_CATEGORIAS,
        ):
            col = db[nombre]

            muestra = col.find_one({}, {"_id": 1})
            total = col.estimated_document_count()

            if muestra is None or total == 0:
                raise ColeccionSinDatos()

            resultado[nombre] = {
                "lectura": "ok",
                "documentos": total,
            }

    return resultado


def crear_producto(datos):
    ahora = datetime.now(timezone.utc)

    producto = {
        "_id": f"prod_{uuid4().hex[:12]}",
        "nombre": datos["nombre"],
        "descripcion": datos["descripcion"],
        "precio": datos["precio"],
        "moneda": "CLP",
        "stock_fisico": datos["stock_fisico"],
        "stock_reservado": 0,
        "categoria_id": datos["categoria_id"],
        "imagenes": datos.get("imagenes", []),
        "activo": True,
        "version": 1,
        "creado_en": ahora,
        "actualizado_en": ahora,
    }

    with errores_mongo():
        get_productos().insert_one(producto)

    return producto


def actualizar_producto(producto_id, datos):
    ahora = datetime.now(timezone.utc)

    with errores_mongo():
        coleccion = get_productos()

        cambios = dict(datos)
        cambios["actualizado_en"] = ahora

        resultado = coleccion.find_one_and_update(
            {"_id": producto_id},
            {
                "$set": cambios,
                "$inc": {"version": 1},
            },
            return_document=ReturnDocument.AFTER,
        )

    return resultado


def crear_categoria(datos):
    categoria = {
        "_id": datos["identificador"],
        "nombre": datos["nombre"],
        "descripcion": datos.get("descripcion", ""),
        "orden": datos["orden"],
        "activa": datos.get("activa", True),
    }

    with errores_mongo():
        get_categorias().insert_one(categoria)

    return categoria


def actualizar_categoria(categoria_id, datos):
    with errores_mongo():
        categoria = get_categorias().find_one_and_update(
            {"_id": categoria_id},
            {"$set": datos},
            return_document=ReturnDocument.AFTER,
        )

    return categoria

def ajustar_inventario(producto_id, stock_nuevo, motivo, administrador):
    ahora = datetime.now(timezone.utc)

    ajuste = {
        "ajuste_id": f"ajuste_{uuid4().hex}",
        "producto_id": producto_id,
        "stock_anterior": "$stock_fisico",
        "stock_nuevo": stock_nuevo,
        "motivo": {"$literal": motivo},
        "administrador_id": administrador["id"],
        "administrador_nombre": {
            "$literal": (
                f"{administrador['nombre']} "
                f"{administrador['apellido']}"
            ).strip()
        },
        "administrador_correo": {
            "$literal": administrador["correo"]
        },
        "fecha": ahora,
    }

    with errores_mongo():
        producto = get_productos().find_one_and_update(
            {
                "_id": producto_id,
                "stock_reservado": {"$lte": stock_nuevo},
            },
            [
                {
                    "$set": {
                        "historial_ajustes": {
                            "$concatArrays": [
                                {
                                    "$ifNull": [
                                        "$historial_ajustes",
                                        []
                                    ]
                                },
                                [ajuste]
                            ]
                        },
                        "stock_fisico": stock_nuevo,
                        "actualizado_en": ahora,
                        "version": {
                            "$add": [
                                {"$ifNull": ["$version", 0]},
                                1
                            ]
                        },
                    }
                }
            ],
            return_document=ReturnDocument.AFTER,
        )

    return producto
