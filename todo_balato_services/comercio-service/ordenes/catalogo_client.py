import requests
from django.conf import settings


class CatalogoError(Exception):
    """Error base al consultar el servicio de Catálogo."""


class ProductoNoEncontradoError(CatalogoError):
    """El producto no existe o no está disponible en Catálogo (404)."""


class RespuestaCatalogoInvalidaError(CatalogoError):
    """La respuesta de Catálogo no tiene JSON válido o campos esperados."""


class CatalogoNoDisponibleError(CatalogoError):
    """Catálogo no responde, excedió el timeout o devolvió error de servidor."""


def _resolver_stock_disponible(data):
    if "stock_disponible" in data and data["stock_disponible"] is not None:
        return int(data["stock_disponible"])
    if "stock" in data and data["stock"] is not None:
        return int(data["stock"])
    if "stock_fisico" in data and data["stock_fisico"] is not None:
        fisico = int(data["stock_fisico"])
        reservado = int(data.get("stock_reservado", 0) or 0)
        return fisico - reservado
    raise RespuestaCatalogoInvalidaError("Falta información de stock en Catálogo.")


def obtener_producto(producto_id):
    base_url = settings.CATALOGO_API_URL.rstrip("/")
    url = f"{base_url}/productos/{producto_id}"

    try:
        response = requests.get(url, timeout=5)
    except requests.Timeout as exc:
        raise CatalogoNoDisponibleError("Timeout al consultar el servicio de Catálogo.") from exc
    except requests.RequestException as exc:
        raise CatalogoNoDisponibleError(f"No se pudo conectar con Catálogo: {exc}") from exc

    if response.status_code == 404:
        raise ProductoNoEncontradoError(f"Producto {producto_id} no encontrado en Catálogo.")

    if response.status_code >= 500 or response.status_code >= 400:
        raise CatalogoNoDisponibleError(
            f"Catálogo devolvió un estado HTTP no esperado ({response.status_code})."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RespuestaCatalogoInvalidaError("La respuesta de Catálogo no es un JSON válido.") from exc

    if not isinstance(data, dict):
        raise RespuestaCatalogoInvalidaError("La estructura JSON de Catálogo no es un objeto.")

    if "nombre" not in data or "precio" not in data:
        raise RespuestaCatalogoInvalidaError("Faltan campos mínimos (nombre o precio) en Catálogo.")

    stock_disponible = _resolver_stock_disponible(data)

    return {
        "identificador": data.get("id", data.get("identificador", producto_id)),
        "nombre": data["nombre"],
        "precio": data["precio"],
        "moneda": data.get("moneda", "CLP"),
        "estado": data.get("estado", "ACTIVO"),
        "stock_disponible": stock_disponible,
        "stock_fisico": data.get("stock_fisico", stock_disponible),
        "stock_reservado": data.get("stock_reservado", 0),
    }
