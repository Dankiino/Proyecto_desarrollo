import os
from pymongo import MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ["CATALOGO_MONGO_URI"])
    return _client.get_database("catalogo_db")


def obtener_producto(producto_id):
    db = get_db()
    return db.productos.find_one({"_id": producto_id, "activo": True})