import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .authentication import UsuarioRemoto
from .models import Orden
from .views import CarritoCalcularView, CheckoutView


class CheckoutTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.cliente = UsuarioRemoto(
            {"user_id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "ACTIVO"}
        )
        self.items = [{"producto_id": "producto-1", "cantidad": 2}]
        self.lineas = [
            {
                "producto_id": "producto-1",
                "nombre": "Producto",
                "precio_unitario": 10,
                "cantidad": 2,
                "subtotal": 20,
                "problema": None,
            }
        ]

    def checkout(self, items=None, user=None, key="intento-1", total=20):
        payload = {
            "items": self.items if items is None else items,
            "total_esperado": total,
        }
        request = self.factory.post(
            "/api/checkout",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        if user is not None:
            force_authenticate(request, user=user)
        return CheckoutView.as_view()(request)

    def test_checkout_rejects_empty_or_invalid_quantities(self):
        casos = [
            [],
            [{"producto_id": "producto-1", "cantidad": 0}],
            [{"producto_id": "producto-1", "cantidad": -1}],
            [{"producto_id": "producto-1", "cantidad": 1.5}],
            [{"producto_id": "producto-1", "cantidad": True}],
        ]
        for items in casos:
            with self.subTest(items=items):
                respuesta = self.checkout(items=items, user=self.cliente)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.data["error"]["codigo"], "validacion")

    def test_checkout_rejects_duplicate_products(self):
        items = [
            {"producto_id": "producto-1", "cantidad": 1},
            {"producto_id": "producto-1", "cantidad": 2},
        ]
        respuesta = self.checkout(items=items, user=self.cliente)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("repetido", respuesta.data["error"]["campos"]["items[1].producto_id"][0])

    @patch("ordenes.views.calcular_lineas")
    def test_same_idempotency_key_and_order_returns_same_order(self, calcular):
        calcular.return_value = (self.lineas, 20, True)

        primera = self.checkout(user=self.cliente)
        segunda = self.checkout(user=self.cliente)

        self.assertEqual(primera.status_code, 201)
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(primera.data["orden"]["id"], segunda.data["orden"]["id"])
        self.assertEqual(Orden.objects.count(), 1)
        calcular.assert_called_once()

    @patch("ordenes.views.calcular_lineas")
    def test_same_idempotency_key_with_different_order_is_rejected(self, calcular):
        calcular.return_value = (self.lineas, 20, True)
        primera = self.checkout(user=self.cliente)
        items_distintos = [{"producto_id": "producto-2", "cantidad": 2}]

        segunda = self.checkout(items=items_distintos, user=self.cliente)

        self.assertEqual(primera.status_code, 201)
        self.assertEqual(segunda.status_code, 409)
        self.assertEqual(segunda.data["error"]["codigo"], "conflicto")
        self.assertEqual(Orden.objects.count(), 1)

    @patch("ordenes.views.calcular_lineas")
    def test_same_idempotency_key_cannot_reveal_another_customers_order(self, calcular):
        calcular.return_value = (self.lineas, 20, True)
        self.checkout(user=self.cliente)
        otro_cliente = UsuarioRemoto(
            {"user_id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "ACTIVO"}
        )

        respuesta = self.checkout(user=otro_cliente)

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.data["error"]["codigo"], "conflicto")
        self.assertEqual(Orden.objects.count(), 1)

    @patch("ordenes.views.calcular_lineas")
    def test_price_change_returns_updated_total_without_creating_order(self, calcular):
        calcular.return_value = (self.lineas, 20, True)

        respuesta = self.checkout(user=self.cliente, total=19)

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.data["error"]["codigo"], "precio_cambiado")
        self.assertEqual(respuesta.data["error"]["carrito"]["total"], 20)
        self.assertEqual(Orden.objects.count(), 0)

    def test_checkout_rejects_visitors_administrators_and_blocked_accounts(self):
        visitantes = self.checkout()
        admin = UsuarioRemoto(
            {"user_id": str(uuid.uuid4()), "rol": "ADMIN", "estado": "ACTIVO"}
        )
        bloqueado = UsuarioRemoto(
            {"user_id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "BLOQUEADO"}
        )

        respuesta_admin = self.checkout(user=admin, key="admin-key")
        respuesta_bloqueado = self.checkout(user=bloqueado, key="blocked-key")

        self.assertEqual(visitantes.status_code, 401)
        self.assertEqual(respuesta_admin.status_code, 403)
        self.assertEqual(respuesta_bloqueado.status_code, 403)
