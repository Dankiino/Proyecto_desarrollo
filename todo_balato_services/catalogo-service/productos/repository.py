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
        return list(get_categorias().find(filtro).sort("orden", 1))


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
):
    filtro = {}
    if solo_activos:
        filtro["activo"] = True
    if categoria_id:
        filtro["$or"] = [
            {"categoria_id": categoria_id},
            {"categoria_ids": categoria_id},
            {"categorias.id": categoria_id},
            {"categorias": categoria_id},
        ]
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
        "recientes": [("actualizado_en", -1), ("_id", -1)],
        "precio_asc": [("precio", 1), ("_id", 1)],
        "precio_desc": [("precio", -1), ("_id", -1)],
        "nombre_asc": [("nombre", 1), ("_id", 1)],
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
        for nombre in (COLECCION_PRODUCTOS, COLECCION_CATEGORIAS):
            col = db[nombre]
            muestra = col.find_one({}, {"_id": 1})
            total = col.estimated_document_count()
            if muestra is None or total == 0:
                raise ColeccionSinDatos()
            resultado[nombre] = {"lectura": "ok", "documentos": total}
    return resultado