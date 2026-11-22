import json
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


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


def main():
    if len(sys.argv) < 2:
        print("Uso: python importar_mock.py <ruta_json>")
        return

    ruta = sys.argv[1]
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)

    print("Llaves del archivo:", list(datos.keys()))
    cats = [convertir(c) for c in datos.get("categorias", [])]
    prods = [convertir(p) for p in datos.get("productos", [])]
    print(f"Categorias preparadas: {len(cats)} | Productos preparados: {len(prods)}")
    print("La carga en MongoDB corresponde exclusivamente a catalogo-service.")


if __name__ == "__main__":
    main()
