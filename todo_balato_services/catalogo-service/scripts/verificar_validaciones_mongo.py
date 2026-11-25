"""Inspecciona validadores e índices de MongoDB y ejecuta pruebas repetibles."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, WriteError

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PREFIJO = f"tmp-test-{uuid.uuid4().hex[:8]}"


def _imagenes(n: int) -> list[dict]:
    return [
        {"url": f"https://example.com/img-{i}.jpg", "alt": f"Imagen de prueba {i}"}
        for i in range(1, n + 1)
    ]


def _producto_base(prod_id: str, **cambios) -> dict:
    ahora = datetime.now(timezone.utc)
    doc = {
        "_id": prod_id,
        "nombre": "Producto de prueba",
        "descripcion": "Documento temporal para validar reglas de MongoDB.",
        "precio": 1990,
        "moneda": "CLP",
        "stock_fisico": 10,
        "stock_reservado": 2,
        "categoria_id": "hogar",
        "imagenes": _imagenes(4),
        "activo": True,
        "version": 1,
        "creado_en": ahora,
        "actualizado_en": ahora,
    }
    doc.update(cambios)
    return doc


def _categoria_base(cat_id: str, **cambios) -> dict:
    doc = {
        "_id": cat_id,
        "nombre": "Categoría prueba",
        "descripcion": "Categoría temporal de prueba",
        "orden": 99,
        "activa": True,
    }
    doc.update(cambios)
    return doc


def inspeccionar(db) -> dict:
    info = {
        c["name"]: c.get("options", {})
        for c in db.command("listCollections")["cursor"]["firstBatch"]
    }
    resumen = {}
    for nombre in ("productos", "categorias"):
        assert nombre in info, f"No existe la colección esperada: {nombre}"
        opts = info[nombre]
        indices = sorted(db[nombre].index_information().keys())
        conteo = db[nombre].count_documents({})
        resumen[nombre] = {
            "conteo": conteo,
            "validationLevel": opts.get("validationLevel"),
            "validationAction": opts.get("validationAction"),
            "tiene_validador": bool(opts.get("validator")),
            "indices": indices,
        }
        print(
            f"[INFO] {nombre}: {conteo} docs | "
            f"validador={resumen[nombre]['tiene_validador']} "
            f"({resumen[nombre]['validationLevel']}/{resumen[nombre]['validationAction']}) | "
            f"indices={indices}"
        )

    assert resumen["productos"]["tiene_validador"], "Falta validador en productos"
    assert resumen["categorias"]["tiene_validador"], "Falta validador en categorias"
    assert "activo_1_categoria_id_1" in resumen["productos"]["indices"], (
        "Falta el índice { activo: 1, categoria_id: 1 } en productos"
    )
    return resumen


def probar_aceptado(col, doc: dict, etiqueta: str, creados: list[str]) -> bool:
    try:
        col.insert_one(doc)
        creados.append(doc["_id"])
        print(f"  [OK] Aceptado: {etiqueta}")
        return True
    except Exception as exc:
        print(f"  [FALLO] Debía aceptar ({etiqueta}), pero falló: {exc}")
        return False


def probar_rechazado(
    col, doc: dict, etiqueta: str, creados: list[str], esperado=(WriteError,)
) -> bool:
    try:
        col.insert_one(doc)
        creados.append(doc["_id"])
        print(f"  [FALLO] Debía rechazar ({etiqueta}), pero MongoDB lo aceptó")
        return False
    except esperado as exc:
        codigo = getattr(exc, "code", None)
        print(f"  [OK] Rechazado (código {codigo}): {etiqueta}")
        return True


def main() -> int:
    uri = os.environ.get("CATALOGO_MONGO_URI")
    db_name = os.getenv("CATALOGO_DB_NAME", "catalogo_db")
    if not uri:
        print("ERROR: falta CATALOGO_MONGO_URI en el entorno o en .env", file=sys.stderr)
        return 2

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    print("=== 1. Inspección de colecciones existentes ===")
    antes = inspeccionar(db)

    creados_prod: list[str] = []
    creados_cat: list[str] = []
    resultados: list[bool] = []

    try:
        print("\n=== 2. Pruebas en colección productos ===")
        id_4 = f"{PREFIJO}-p4"
        id_6 = f"{PREFIJO}-p6"
        resultados.append(
            probar_aceptado(db.productos, _producto_base(id_4, imagenes=_imagenes(4)), "producto válido con 4 imágenes", creados_prod)
        )
        resultados.append(
            probar_aceptado(db.productos, _producto_base(id_6, imagenes=_imagenes(6)), "producto válido con 6 imágenes", creados_prod)
        )

        casos_invalidos_prod = [
            ("precio 0", _producto_base(f"{PREFIJO}-inv1", precio=0)),
            ("precio con decimales", _producto_base(f"{PREFIJO}-inv2", precio=1990.5)),
            ("moneda distinta de CLP", _producto_base(f"{PREFIJO}-inv3", moneda="USD")),
            ("stock físico negativo", _producto_base(f"{PREFIJO}-inv4", stock_fisico=-1, stock_reservado=0)),
            ("stock reservado mayor al físico", _producto_base(f"{PREFIJO}-inv5", stock_fisico=2, stock_reservado=5)),
            ("solo 3 imágenes", _producto_base(f"{PREFIJO}-inv6", imagenes=_imagenes(3))),
            ("7 imágenes", _producto_base(f"{PREFIJO}-inv7", imagenes=_imagenes(7))),
            ("imagen sin alt", _producto_base(f"{PREFIJO}-inv8", imagenes=_imagenes(3) + [{"url": "https://example.com/x.jpg"}])),
            ("imagen con URL no http(s)", _producto_base(f"{PREFIJO}-inv9", imagenes=_imagenes(3) + [{"url": "ftp://example.com/x.jpg", "alt": "Foto"}])),
        ]
        for etiqueta, doc in casos_invalidos_prod:
            resultados.append(probar_rechazado(db.productos, doc, etiqueta, creados_prod))

        resultados.append(
            probar_rechazado(
                db.productos,
                _producto_base(id_4),
                "_id repetido en productos",
                creados_prod,
                esperado=(DuplicateKeyError,),
            )
        )

        print("\n=== 3. Pruebas en colección categorias ===")
        cat_ok = f"{PREFIJO}-cat"
        resultados.append(
            probar_aceptado(db.categorias, _categoria_base(cat_ok), "categoría válida", creados_cat)
        )

        casos_invalidos_cat = [
            ("_id con mayúsculas y espacio", _categoria_base(f"{PREFIJO} Malo")),
            ("nombre de 1 carácter", _categoria_base(f"{PREFIJO}-c1", nombre="A")),
            ("orden negativo", _categoria_base(f"{PREFIJO}-c2", orden=-1)),
            ("activa no booleano", _categoria_base(f"{PREFIJO}-c3", activa="si")),
        ]
        for etiqueta, doc in casos_invalidos_cat:
            resultados.append(probar_rechazado(db.categorias, doc, etiqueta, creados_cat))

    finally:
        if creados_prod:
            db.productos.delete_many({"_id": {"$in": creados_prod}})
        if creados_cat:
            db.categorias.delete_many({"_id": {"$in": creados_cat}})
        print("\n=== 4. Limpieza y verificación de integridad ===")
        despues_prod = db.productos.count_documents({})
        despues_cat = db.categorias.count_documents({})
        print(
            f"[INFO] Documentos preservados -> productos: {despues_prod} "
            f"(antes {antes['productos']['conteo']}), categorias: {despues_cat} "
            f"(antes {antes['categorias']['conteo']})"
        )
        client.close()

    total = len(resultados)
    aprobadas = sum(resultados)
    print(f"\nResultado final: {aprobadas}/{total} pruebas aprobadas.")
    return 0 if aprobadas == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
