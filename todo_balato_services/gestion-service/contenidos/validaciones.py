"""Reglas de validación de los contenidos editables.

Cada `ContenidoPagina` existente es un campo editable; aquí solo se valida el
valor recibido según el tipo del registro (texto, imagen o enlace) y, cuando
corresponde, una regla específica de la página/clave.
"""

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator

MAX_TEXTO = 2000
MAX_URL = 500
MAX_ALT = 200

_validar_url = URLValidator(schemes=["http", "https"])
_validar_correo = EmailValidator()

# Reglas adicionales por (pagina, clave).
REGLAS_ESPECIALES = {
    ("contacto", "correo"): "correo",
}


def _validar_ruta_o_url(valor):
    """Acepta rutas internas (/catalogo, /logo.png) o URLs http(s) absolutas."""
    if valor.startswith("/") and not valor.startswith("//"):
        if any(c.isspace() for c in valor):
            return "La ruta no puede contener espacios."
        return None
    try:
        _validar_url(valor)
    except ValidationError:
        return "Ingresa una URL http(s) válida o una ruta que empiece con «/»."
    return None


def validar_contenido(contenido, datos):
    """Valida `datos` ({valor, texto_alternativo}) para el `ContenidoPagina` dado.

    Devuelve (valores_limpios, errores). `errores` es un dict campo -> [mensajes].
    """
    errores = {}
    valor = datos.get("valor", contenido.valor)
    alt = datos.get("texto_alternativo", contenido.texto_alternativo)

    if not isinstance(valor, str):
        errores["valor"] = ["Debe ser texto."]
        valor = ""
    if alt is None:
        alt = ""
    if not isinstance(alt, str):
        errores["texto_alternativo"] = ["Debe ser texto."]
        alt = ""

    valor = valor.strip()
    alt = alt.strip()

    if "valor" not in errores:
        if not valor:
            errores["valor"] = ["Este campo es obligatorio."]
        elif contenido.tipo == "texto":
            if len(valor) > MAX_TEXTO:
                errores["valor"] = [f"Máximo {MAX_TEXTO} caracteres."]
            elif REGLAS_ESPECIALES.get((contenido.pagina, contenido.clave)) == "correo":
                try:
                    _validar_correo(valor)
                except ValidationError:
                    errores["valor"] = ["Ingresa un correo electrónico válido."]
        else:  # imagen o enlace
            if len(valor) > MAX_URL:
                errores["valor"] = [f"Máximo {MAX_URL} caracteres."]
            else:
                mensaje = _validar_ruta_o_url(valor)
                if mensaje:
                    errores["valor"] = [mensaje]

    if "texto_alternativo" not in errores:
        if contenido.tipo == "imagen" and not alt:
            errores["texto_alternativo"] = ["Describe la imagen (texto alternativo obligatorio)."]
        elif len(alt) > MAX_ALT:
            errores["texto_alternativo"] = [f"Máximo {MAX_ALT} caracteres."]

    return {"valor": valor, "texto_alternativo": alt}, errores
