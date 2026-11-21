import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

mongo_uri = os.getenv("CATALOGO_MONGO_URI")
database_name = os.getenv("CATALOGO_DB_NAME", "catalogo_db")

if not mongo_uri:
    raise SystemExit("Falta CATALOGO_MONGO_URI en catalogo-service/.env.")

try:
    with MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        collections = client[database_name].list_collection_names()
except OperationFailure as error:
    if error.code == 18:
        raise SystemExit(
            "MongoDB rechazó la autenticación. Revisa el usuario y la contraseña de Atlas."
        ) from None
    raise SystemExit(
        f"MongoDB rechazó la operación (código {error.code}). Revisa los permisos del usuario."
    ) from None
except PyMongoError as error:
    raise SystemExit(
        f"No se pudo completar la conexión con MongoDB ({type(error).__name__}). "
        "Revisa la URI y Network Access en Atlas."
    ) from None

print(f"Conexión y autenticación correctas; base {database_name} accesible.")
print(f"Colecciones visibles: {len(collections)}.")
