from django.conf import settings
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction


def _tx():
    if not (settings.WEBPAY_COMMERCE_CODE and settings.WEBPAY_API_KEY and settings.WEBPAY_RETURN_URL):
        raise RuntimeError("Webpay no está configurado.")
    # Siempre ambiente de prueba: nunca se cobra dinero real.
    return Transaction(WebpayOptions(settings.WEBPAY_COMMERCE_CODE, settings.WEBPAY_API_KEY, IntegrationType.TEST))


def crear(buy_order, session_id, monto):
    return _tx().create(buy_order, session_id, monto, settings.WEBPAY_RETURN_URL)


def confirmar(token):
    return _tx().commit(token)


def consultar(token):
    return _tx().status(token)
