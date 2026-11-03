import json, os, sys
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
ruta = sys.argv[1]
datos = json.load(open(ruta, encoding="utf-8"))
print("Llaves del archivo:", list(datos.keys()))

db = MongoClient(os.environ["CATALOGO_MONGO_URI"]).get_database("catalogo_db")

def fecha(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def convertir(doc):
    doc = dict(doc)
    if "id" in doc:
        doc["_id"] = doc.pop("id")
    for campo in ("creado_en", "actualizado_en"):
        if isinstance(doc.get(campo), str):
            doc[campo] = fecha(doc[campo])
    return doc

cats = [convertir(c) for c in datos["categorias"]]
prods = [convertir(p) for p in datos["productos"]]
db.categorias.insert_many(cats)
db.productos.insert_many(prods)
print("Categorías:", db.categorias.count_documents({}))
print("Productos:", db.productos.count_documents({}))