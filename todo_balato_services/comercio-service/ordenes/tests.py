from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase
from rest_framework import exceptions

from .authentication import IdentidadNoDisponible, JWTRemotoAuthentication
from .permissions import EsClienteActivo


def respuesta(status, datos=None):
    return Mock(status_code=status, json=Mock(return_value=datos))


class AutenticacionRemotaTests(SimpleTestCase):
    def autenticar(self, **kwargs):
        with patch("ordenes.authentication.requests.get", **kwargs):
            return JWTRemotoAuthentication().get_user("token")

    def test_usa_el_estado_vigente_que_informa_gestion(self):
        u = self.autenticar(return_value=respuesta(200, {"id": "1", "rol": "CLIENTE", "estado": "ACTIVO"}))
        self.assertEqual((u.id, u.rol, u.estado), ("1", "CLIENTE", "ACTIVO"))

    def test_cuenta_bloqueada_o_sesion_invalida_se_rechaza(self):
        for status in (401, 403):
            with self.assertRaises(exceptions.AuthenticationFailed):
                self.autenticar(return_value=respuesta(status))

    def test_si_gestion_no_responde_no_se_asume_activa(self):
        with self.assertRaises(IdentidadNoDisponible):
            self.autenticar(side_effect=requests.ConnectionError())
        with self.assertRaises(IdentidadNoDisponible):
            self.autenticar(return_value=respuesta(500))

    def test_solo_el_cliente_activo_compra(self):
        permiso = EsClienteActivo()
        usuario = lambda rol, estado: Mock(is_authenticated=True, rol=rol, estado=estado)
        compra = lambda rol, estado: permiso.has_permission(Mock(user=usuario(rol, estado)), None)
        self.assertTrue(compra("CLIENTE", "ACTIVO"))
        self.assertFalse(compra("CLIENTE", "BLOQUEADO"))
        self.assertFalse(compra("CLIENTE", "PENDIENTE"))
        self.assertFalse(compra("ADMIN", "ACTIVO"))
