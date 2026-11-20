import logging
import threading
from contextlib import contextmanager

from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, OperationFailure, PyMongoError

logger = logging.getLogger(__name__)

COLECCION_PRODUCTOS = "productos"
COLECCION_CATEGORIAS = "categorias"

_client = None
_lock = threading.Lock()


class CatalogoDBError(Exception):
    """Error de acceso a MongoDB. El mensaje es seguro para devolver al cliente."""

    mensaje = "No se pudo acceder a la base de datos del catálogo."


class MongoNoConfigurado(CatalogoDBError):
    mensaje = "La conexión a MongoDB no está configurada en el servicio."


class MongoNoDisponible(CatalogoDBError):
    mensaje = "No se pudo conectar con MongoDB."


class MongoAccesoDenegado(CatalogoDBError):
    mensaje = "MongoDB rechazó la conexión o los permisos del servicio."


class ColeccionSinDatos(CatalogoDBError):
    mensaje = "Una colección del catálogo no tiene documentos o la base configurada no es la correcta."


@contextmanager
def errores_mongo():
    """Traduce errores de pymongo a errores propios.

    Nunca se usa str(exc) ni se encadena la excepción original: los mensajes de
    pymongo pueden incluir hosts o fragmentos de la URI.
    """
    try:
        yield
    except CatalogoDBError:
        raise
    except OperationFailure as exc:  # credenciales o permisos rechazados
        logger.error("MongoDB rechazó la operación (%s, code=%s)", type(exc).__name__, exc.code)
        raise MongoAccesoDenegado() from None
    except ConfigurationError as exc:  # URI inválida, DNS SRV, etc.
        logger.error("Configuración de MongoDB inválida (%s)", type(exc).__name__)
        raise MongoNoConfigurado() from None
    except PyMongoError as exc:  # timeouts, red caída, servidor inaccesible
        logger.error("MongoDB no disponible (%s)", type(exc).__name__)
        raise MongoNoDisponible() from None


def get_client():
    global _client
    uri = settings.CATALOGO_MONGO_URI
    if not uri:
        raise MongoNoConfigurado()
    if _client is None:
        with _lock:
            if _client is None:
                with errores_mongo():
                    _client = MongoClient(
                        uri,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=10000,
                        appname="catalogo-service",
                    )
    return _client


def reset_client():
    """Cierra y descarta el cliente (útil en pruebas)."""
    global _client
    with _lock:
        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass
        _client = None


def get_db():
    return get_client()[settings.CATALOGO_DB_NAME]


def get_productos():
    return get_db()[COLECCION_PRODUCTOS]


def get_categorias():
    return get_db()[COLECCION_CATEGORIAS]