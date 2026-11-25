import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from . import inventario
from .authentication import UsuarioRemoto
from .catalogo_client import CatalogoNoDisponibleError
from .models import DetalleOrden, Orden
from .views import CheckoutView


class CheckoutTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.cliente = UsuarioRemoto(
            {"id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "ACTIVO"}
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
        self.reservar_patcher = patch("ordenes.views.inventario.reservar")
        self.reservar = self.reservar_patcher.start()
        self.addCleanup(self.reservar_patcher.stop)

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
        self.reservar.assert_called_once()
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
            {"id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "ACTIVO"}
        )

        respuesta = self.checkout(user=otro_cliente)

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.data["error"]["codigo"], "conflicto")
        self.assertEqual(Orden.objects.count(), 1)

    @patch("ordenes.views.calcular_lineas")
    def test_price_change_returns_updated_total_without_creating_order(self, calcular):
        lineas_actualizadas = [{
            **self.lineas[0],
            "precio_unitario": 12,
            "subtotal": 24,
        }]
        calcular.return_value = (lineas_actualizadas, 24, True)

        respuesta = self.checkout(user=self.cliente, total=19)

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.data["error"]["codigo"], "precio_cambiado")
        self.assertEqual(respuesta.data["error"]["carrito"]["total"], 24)
        self.assertEqual(
            respuesta.data["error"]["carrito"]["lineas"][0]["precio_unitario"],
            12,
        )
        self.assertEqual(Orden.objects.count(), 0)

    @patch("ordenes.views.calcular_lineas")
    def test_inventory_reservation_happens_before_order_creation(self, calcular):
        calcular.return_value = (self.lineas, 20, True)

        def reservar_antes_de_crear(reserva):
            self.assertFalse(Orden.objects.filter(idempotency_key="intento-1").exists())
            self.assertEqual(reserva.lineas[0].producto_id, "producto-1")
            self.assertEqual(reserva.lineas[0].cantidad, 2)

        self.reservar.side_effect = reservar_antes_de_crear

        respuesta = self.checkout(user=self.cliente)

        self.assertEqual(respuesta.status_code, 201)
        self.reservar.assert_called_once()
        self.assertEqual(Orden.objects.count(), 1)

    @patch("ordenes.views.calcular_lineas")
    def test_failed_inventory_reservation_does_not_create_order(self, calcular):
        calcular.return_value = (self.lineas, 20, True)
        self.reservar.side_effect = inventario.InventarioNoDisponible("Sin stock")

        respuesta = self.checkout(user=self.cliente)

        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.data["error"]["codigo"], "inventario_no_disponible")
        self.assertEqual(Orden.objects.count(), 0)

    @patch("ordenes.views.calcular_lineas")
    def test_insufficient_stock_does_not_reserve_or_create_order(self, calcular):
        lineas = [{**self.lineas[0], "problema": "stock_insuficiente", "subtotal": 0}]
        calcular.return_value = (lineas, 0, False)

        respuesta = self.checkout(user=self.cliente, total=0)

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.data["error"]["codigo"], "carrito_inconsistente")
        self.assertEqual(Orden.objects.count(), 0)
        self.reservar.assert_not_called()

    @patch("ordenes.views.calcular_lineas")
    def test_catalogo_unavailable_returns_503_without_creating_order(self, calcular):
        calcular.side_effect = CatalogoNoDisponibleError("Catálogo no responde")

        respuesta = self.checkout(user=self.cliente)

        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.data["error"]["codigo"], "catalogo_no_disponible")
        self.assertEqual(Orden.objects.count(), 0)
        self.reservar.assert_not_called()

    @patch("ordenes.views.calcular_lineas")
    def test_order_lines_keep_name_price_quantity_and_total_snapshot(self, calcular):
        lineas_precio_inicial = [dict(self.lineas[0])]
        lineas_precio_nuevo = [{
            **self.lineas[0],
            "nombre": "Producto renombrado",
            "precio_unitario": 12,
            "subtotal": 24,
        }]
        calcular.side_effect = [
            (lineas_precio_inicial, 20, True),
            (lineas_precio_nuevo, 24, True),
        ]

        primera = self.checkout(user=self.cliente, key="snapshot-1")
        segunda = self.checkout(user=self.cliente, key="snapshot-2", total=24)

        self.assertEqual((primera.status_code, segunda.status_code), (201, 201))
        primera_orden = Orden.objects.get(id=primera.data["orden"]["id"])
        primera_linea = DetalleOrden.objects.get(orden=primera_orden)
        self.assertEqual(primera_orden.total, 20)
        self.assertEqual(primera_linea.nombre_producto, "Producto")
        self.assertEqual(primera_linea.precio_unitario, 10)
        self.assertEqual(primera_linea.cantidad, 2)
        self.assertEqual(primera_linea.subtotal, 20)
        self.assertEqual(Orden.objects.get(id=segunda.data["orden"]["id"]).total, 24)

    def test_checkout_rejects_visitors_administrators_and_blocked_accounts(self):
        visitantes = self.checkout()
        admin = UsuarioRemoto(
            {"id": str(uuid.uuid4()), "rol": "ADMIN", "estado": "ACTIVO"}
        )
        bloqueado = UsuarioRemoto(
            {"id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "BLOQUEADO"}
        )

        respuesta_admin = self.checkout(user=admin, key="admin-key")
        respuesta_bloqueado = self.checkout(user=bloqueado, key="blocked-key")

        self.assertEqual(visitantes.status_code, 401)
        self.assertEqual(respuesta_admin.status_code, 403)
        self.assertEqual(respuesta_bloqueado.status_code, 403)
