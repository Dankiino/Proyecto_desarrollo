from .mongo import (
    COLECCION_CATEGORIAS,
    COLECCION_PRODUCTOS,
    ColeccionSinDatos,
    errores_mongo,
    get_categorias,
    get_db,
    get_productos,
)
from datetime import datetime, timezone
from uuid import uuid4
from pymongo import ReturnDocument
import re



def listar_categorias(solo_activas=True):
    filtro = {"activa": True} if solo_activas else {}
    with errores_mongo():
        return list(get_categorias().find(filtro).sort("orden", 1))


def obtener_categoria(slug, solo_activas=True):
    filtro = {"_id": slug}
    if solo_activas:
        filtro["activa"] = True
    with errores_mongo():
        return get_categorias().find_one(filtro)



def listar_productos(
    categoria_id=None,
    solo_activos=True,
    pagina=1,
    tamano=20,
    buscar=None
):
    filtro = {}

    if solo_activos:
        filtro["activo"] = True

    if categoria_id:
        filtro["categoria_id"] = categoria_id

    if buscar and buscar.strip():
        texto = re.escape(buscar.strip())

        filtro["$or"] = [
            {"nombre": {"$regex": texto, "$options": "i"}},
            {"descripcion": {"$regex": texto, "$options": "i"}}
        ]

    with errores_mongo():
        col = get_productos()

        total = col.count_documents(filtro)

        items = list(
            col.find(filtro)
            .sort("_id", 1)
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
        for nombre in (COLECCION_PRODUCTOS, COLECCION_CATEGORIAS):
            col = db[nombre]
            muestra = col.find_one({}, {"_id": 1})
            total = col.estimated_document_count()
            if muestra is None or total == 0:
                raise ColeccionSinDatos()
            resultado[nombre] = {"lectura": "ok", "documentos": total}
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
                "$inc": {"version": 1}
            },
            return_document=ReturnDocument.AFTER
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
    from pymongo import ReturnDocument

    with errores_mongo():
        categoria = get_categorias().find_one_and_update(
            {"_id": categoria_id},
            {"$set": datos},
            return_document=ReturnDocument.AFTER
        )

    return categoria
