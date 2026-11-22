from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .authentication import UsuarioRemoto
from .models import Orden, Pago

CLIENTE = "11111111-1111-4111-8111-111111111111"
OK = {"status": "AUTHORIZED", "response_code": 0, "amount": 10000}


def crear_orden(estado_pago="PENDIENTE"):
    orden = Orden.objects.create(cliente_id=CLIENTE, total=10000, idempotency_key="k")
    pago = Pago.objects.create(orden=orden, token_ws="tok", buy_order="O" + orden.id.hex[:25], estado=estado_pago)
    return orden, pago


class PagoWebpayTests(TestCase):
    def setUp(self):
        for nombre in ("webpay", "inventario"):
            p = patch(f"ordenes.pagos.{nombre}")
            setattr(self, nombre, p.start())
            self.addCleanup(p.stop)
        self.orden, self.pago = crear_orden()
        self.webpay.confirmar.return_value = {**OK, "buy_order": self.pago.buy_order}

    def retorno(self, **params):
        return self.client.get("/api/pagos/webpay/retorno", params)

    def estados(self):
        self.orden.refresh_from_db(), self.pago.refresh_from_db()
        return self.orden.estado, self.pago.estado

    def test_aprobacion_confirma_con_pago_e_inventario(self):
        r = self.retorno(token_ws="tok")
        self.assertEqual(self.estados(), ("CONFIRMADA", "APROBADO"))
        self.assertNotIn("tok", r["Location"])
        self.assertIn(str(self.orden.id), r["Location"])

    def test_aprobado_sin_consolidar_queda_pendiente_y_se_recupera(self):
        self.inventario.consolidar.side_effect = Exception()
        self.retorno(token_ws="tok")
        self.assertEqual(self.estados(), ("CONFIRMACION_PENDIENTE", "APROBADO"))
        self.inventario.consolidar.side_effect = None
        self.retorno(token_ws="tok")
        self.assertEqual(self.estados(), ("CONFIRMADA", "APROBADO"))
        self.webpay.confirmar.assert_called_once()

    def test_rechazo_libera_stock(self):
        self.webpay.confirmar.return_value = {"status": "FAILED", "response_code": -1}
        self.retorno(token_ws="tok")
        self.assertEqual(self.estados(), ("RECHAZADA", "RECHAZADO"))
        self.inventario.liberar.assert_called_once()
        self.inventario.consolidar.assert_not_called()

    def test_cancelacion_libera_stock_sin_consultar_webpay(self):
        self.retorno(TBK_TOKEN="tok", TBK_ORDEN_COMPRA="x", TBK_ID_SESION="y")
        self.assertEqual(self.estados(), ("CANCELADA", "CANCELADO"))
        self.inventario.liberar.assert_called_once()
        self.webpay.confirmar.assert_not_called()

    def test_respuesta_alterada_no_confirma(self):
        for alterada in ({"amount": 1}, {"buy_order": "otra"}):
            with self.subTest(alterada):
                orden, pago = crear_orden_nueva()
                self.webpay.confirmar.return_value = {**OK, "buy_order": pago.buy_order, **alterada}
                self.retorno(token_ws=pago.token_ws)
                orden.refresh_from_db(), pago.refresh_from_db()
                self.assertEqual((orden.estado, pago.estado), ("REVISION_REQUERIDA", "INCONSISTENTE"))
        self.inventario.consolidar.assert_not_called()

    def test_retorno_repetido_no_duplica_pago_ni_stock(self):
        for _ in range(3):
            self.retorno(token_ws="tok")
        self.webpay.confirmar.assert_called_once()
        self.inventario.consolidar.assert_called_once()

    def test_retorno_repetido_tras_rechazo_no_libera_otra_vez(self):
        self.webpay.confirmar.return_value = {"status": "FAILED", "response_code": -1}
        self.retorno(token_ws="tok"), self.retorno(token_ws="tok")
        self.inventario.liberar.assert_called_once()

    def test_webpay_no_responde_no_aprueba_y_se_puede_revisar_de_nuevo(self):
        self.webpay.confirmar.side_effect = Exception()
        self.retorno(token_ws="tok")
        self.assertEqual(self.estados(), ("PENDIENTE_PAGO", "POR_VERIFICAR"))
        self.webpay.consultar.return_value = {**OK, "buy_order": self.pago.buy_order}
        r = cliente_api().post(f"/api/pagos/{self.orden.id}/reverificar")
        self.assertEqual((r.status_code, self.estados()), (200, ("CONFIRMADA", "APROBADO")))
        self.webpay.confirmar.assert_called_once()  # no se repite el commit

    def test_transaccion_abortada_por_webpay_libera_el_stock(self):
        self.webpay.confirmar.side_effect = Exception()
        self.retorno(token_ws="tok")
        self.webpay.consultar.return_value = {"status": "INITIALIZED"}
        self.webpay.confirmar.side_effect = Exception("('Transaction has an invalid finished state: aborted', 422)")
        cliente_api().post(f"/api/pagos/{self.orden.id}/reverificar")
        self.assertEqual(self.estados(), ("VENCIDA", "CANCELADO"))
        self.inventario.liberar.assert_called_once()

    def test_token_desconocido_no_cambia_nada(self):
        r = self.retorno(token_ws="otro")
        self.assertEqual(self.estados(), ("PENDIENTE_PAGO", "PENDIENTE"))
        self.assertEqual(r.status_code, 302)


def crear_orden_nueva():
    orden = Orden.objects.create(cliente_id=CLIENTE, total=10000, idempotency_key=f"k{Orden.objects.count()}")
    return orden, Pago.objects.create(orden=orden, token_ws=f"t{orden.id.hex}", buy_order="O" + orden.id.hex[:25])


def cliente_api(rol="CLIENTE", id=CLIENTE):
    c = APIClient()
    c.force_authenticate(UsuarioRemoto({"id": id, "rol": rol, "estado": "ACTIVO"}))
    return c


class IniciarPagoTests(TestCase):
    def setUp(self):
        for nombre in ("webpay", "inventario"):
            p = patch(f"ordenes.pagos.{nombre}")
            setattr(self, nombre, p.start())
            self.addCleanup(p.stop)
        self.webpay.crear.return_value = {"token": "tok", "url": "https://webpay.test/init"}
        self.orden = Orden.objects.create(cliente_id=CLIENTE, total=10000, idempotency_key="k")

    def iniciar(self, cliente=None, orden_id=None):
        return (cliente or cliente_api()).post("/api/pagos/iniciar", {"orden_id": str(orden_id or self.orden.id)}, format="json")

    def test_reserva_y_crea_transaccion_con_el_total_del_backend(self):
        r = self.iniciar()
        self.assertEqual((r.status_code, r.data["url"]), (200, "https://webpay.test/init"))
        self.inventario.reservar.assert_called_once()
        self.assertEqual(self.webpay.crear.call_args.args[2], 10000)

    def test_doble_clic_no_crea_otro_intento(self):
        self.iniciar(), self.iniciar()
        self.webpay.crear.assert_called_once()
        self.assertEqual(Pago.objects.count(), 1)

    def test_orden_ajena_o_administrador_se_rechazan(self):
        self.assertEqual(self.iniciar(cliente_api(id="22222222-2222-4222-8222-222222222222")).status_code, 404)
        self.assertEqual(self.iniciar(cliente_api(rol="ADMIN")).status_code, 403)

    def test_sin_reserva_no_se_crea_transaccion(self):
        self.inventario.reservar.side_effect = Exception()
        self.assertEqual(self.iniciar().status_code, 503)
        self.webpay.crear.assert_not_called()
        self.assertEqual(Pago.objects.count(), 0)

    def test_fallo_de_webpay_no_deja_pago(self):
        self.webpay.crear.side_effect = Exception()
        self.assertEqual(self.iniciar().status_code, 503)
        self.assertEqual(Pago.objects.count(), 0)
