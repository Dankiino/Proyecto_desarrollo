import hashlib
import logging
import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import TokenCuenta

logger = logging.getLogger(__name__)

# proposito -> (ruta del frontend, asunto, acción que describe el correo)
ENLACES = {
    "ACTIVACION": ("activar", "Activa tu cuenta de Todo Balato", "activar tu cuenta"),
    "RECUPERACION": ("restablecer-password", "Restablece tu contraseña de Todo Balato", "elegir una nueva contraseña"),
}


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def crear_token(usuario, proposito):
    """Crea un token nuevo y deja sin efecto los anteriores sin usar del mismo propósito."""
    TokenCuenta.objects.filter(usuario=usuario, proposito=proposito, usado_en__isnull=True).delete()
    token = secrets.token_urlsafe(32)
    TokenCuenta.objects.create(
        usuario=usuario,
        proposito=proposito,
        token_hash=_hash(token),
        vence_en=timezone.now() + settings.TOKEN_VIGENCIA[proposito],
    )
    return token


def consumir_token(token, proposito):
    """Marca el token como usado de forma atómica. Devuelve el usuario, o None si el
    token no existe (alterado), venció o ya se usó. Llamar dentro de transaction.atomic()."""
    ahora = timezone.now()
    h = _hash(token)
    usados = TokenCuenta.objects.filter(
        token_hash=h, proposito=proposito, usado_en__isnull=True, vence_en__gt=ahora
    ).update(usado_en=ahora)
    if not usados:
        return None
    return TokenCuenta.objects.select_related("usuario").get(token_hash=h).usuario


def enviar_enlace(usuario, proposito):
    """Genera el token y lo envía por correo. Un fallo de correo no interrumpe la operación."""
    token = crear_token(usuario, proposito)
    ruta, asunto, accion = ENLACES[proposito]
    horas = settings.TOKEN_VIGENCIA[proposito].total_seconds() / 3600
    cuerpo = (
        f"Hola {usuario.nombre},\n\n"
        f"Usa este enlace para {accion}:\n{settings.FRONTEND_URL}/{ruta}?token={token}\n\n"
        f"Vence en {horas:g} h y sirve una sola vez. Si no lo solicitaste, ignora este correo."
    )
    try:
        send_mail(asunto, cuerpo, None, [usuario.correo])
    except Exception:
        logger.error("Fallo el envío de correo de %s (usuario %s)", proposito, usuario.id, exc_info=True)


def revocar_sesiones(usuario):
    """Invalida todos los refresh tokens emitidos al usuario."""
    for t in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=t)
