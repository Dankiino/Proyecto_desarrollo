import copy
import uuid
from unittest.mock import patch

from rest_framework.test import APITestCase

from .authentication import UsuarioRemoto
from .catalogo_client import CatalogoNoDisponibleError, ProductoNoEncontradoError
from .models import LineaCarrito

CATALOGO = {
    "p1": {"nombre": "Vaso", "precio": 1000, "stock_disponible": 10, "estado": "ACTIVO"},
    "p2": {"nombre": "Plato", "precio": 2000, "stock_disponible": 5, "estado": "ACTIVO"},
    "agotado": {"nombre": "Taza", "precio": 500, "stock_disponible": 0, "estado": "ACTIVO"},
    "inactivo": {"nombre": "Jarra", "precio": 700, "stock_disponible": 10, "estado": "INACTIVO"},
}


def cliente_falso():
    return UsuarioRemoto(
        {"user_id": str(uuid.uuid4()), "rol": "CLIENTE", "estado": "ACTIVO"}
    )


class CarritoGuardadoTests(APITestCase):
    def setUp(self):
        self.catalogo = copy.deepcopy(CATALOGO)
        parche = patch("ordenes.views.obtener_producto", side_effect=self._producto)
        parche.start()
        self.addCleanup(parche.stop)
        self.cliente_a = cliente_falso()
        self.cliente_b = cliente_falso()
        self.client.force_authenticate(user=self.cliente_a)

    def _producto(self, producto_id):
        if producto_id not in self.catalogo:
            raise ProductoNoEncontradoError(producto_id)
        return self.catalogo[producto_id]

    def _poner(self, producto_id, cantidad):
        return self.client.put(
            f"/api/carrito/items/{producto_id}", {"cantidad": cantidad}, format="json"
        )

    def _combinar(self, items):
        return self.client.post("/api/carrito/combinar", {"items": items}, format="json")

    def test_requiere_sesion(self):
        self.client.force_authenticate(user=None)
        r = self.client.get("/api/carrito")
        self.assertIn(r.status_code, (401, 403))

    def test_carrito_nuevo_esta_vacio(self):
        r = self.client.get("/api/carrito")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["items"], [])

    def test_agregar_cambiar_cantidad_y_quitar(self):
        r = self._poner("p1", 2)
        self.assertEqual(r.json()["items"], [{"producto_id": "p1", "cantidad": 2}])

        r = self._poner("p1", 5)
        self.assertEqual(r.json()["items"], [{"producto_id": "p1", "cantidad": 5}])

        r = self.client.delete("/api/carrito/items/p1")
        self.assertEqual(r.json()["items"], [])

    def test_cantidad_cero_quita_el_producto(self):
        self._poner("p1", 2)
        r = self._poner("p1", 0)
        self.assertEqual(r.json()["items"], [])

    def test_repetir_operacion_no_duplica_lineas(self):
        self._poner("p1", 2)
        self._poner("p1", 2)
        self._poner("p1", 2)
        self.assertEqual(LineaCarrito.objects.count(), 1)

    def test_cantidades_invalidas_se_rechazan(self):
        for valor in (-1, "a", True, 2.5, 100, None):
            r = self._poner("p1", valor)
            self.assertEqual(r.status_code, 400, msg=f"valor {valor!r}")
        self.assertEqual(LineaCarrito.objects.count(), 0)

    def test_solo_se_guarda_identificador_y_cantidad(self):
        campos = {f.name for f in LineaCarrito._meta.get_fields()}
        self.assertEqual(campos, {"id", "carrito", "producto_id", "cantidad"})

    def test_precio_y_stock_se_consultan_siempre_en_catalogo(self):
        self._poner("p1", 2)
        self.assertEqual(self.client.get("/api/carrito").json()["total"], 2000)

        self.catalogo["p1"]["precio"] = 1500
        self.assertEqual(self.client.get("/api/carrito").json()["total"], 3000)

    def test_combinar_gana_la_mayor_cantidad(self):
        self._poner("p1", 3)
        r = self._combinar([{"producto_id": "p1", "cantidad": 2},
                            {"producto_id": "p2", "cantidad": 1}])
        self.assertEqual(
            r.json()["items"],
            [{"producto_id": "p1", "cantidad": 3}, {"producto_id": "p2", "cantidad": 1}],
        )

        r = self._combinar([{"producto_id": "p1", "cantidad": 7}])
        self.assertIn({"producto_id": "p1", "cantidad": 7}, r.json()["items"])

    def test_combinar_dos_veces_da_el_mismo_resultado(self):
        self._poner("p1", 3)
        anonimo = [{"producto_id": "p1", "cantidad": 2},
                   {"producto_id": "p2", "cantidad": 1}]
        primero = self._combinar(anonimo).json()
        segundo = self._combinar(anonimo).json()
        self.assertEqual(primero, segundo)
        self.assertEqual(LineaCarrito.objects.count(), 2)

    def test_combinar_rechaza_datos_invalidos(self):
        r = self._combinar([{"producto_id": "p1", "cantidad": 0}])
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/carrito/combinar", {"items": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_recuperar_avisa_de_productos_con_problemas(self):
        self._poner("p1", 20)        # stock 10
        self._poner("agotado", 1)
        self._poner("inactivo", 1)
        self._poner("fantasma", 1)   # no existe en Catálogo

        r = self.client.get("/api/carrito").json()
        problemas = {a["producto_id"]: a["problema"] for a in r["avisos"]}
        self.assertEqual(problemas, {
            "p1": "stock_insuficiente",
            "agotado": "agotado",
            "inactivo": "inactivo",
            "fantasma": "no_existe",
        })
        self.assertFalse(r["puede_pagar"])

    def test_cada_cliente_ve_solo_su_carrito(self):
        self._poner("p1", 2)

        self.client.force_authenticate(user=self.cliente_b)
        self.assertEqual(self.client.get("/api/carrito").json()["items"], [])
        self._poner("p2", 4)
        self.client.delete("/api/carrito/items/p1")  # B no tiene p1: no afecta a A

        self.client.force_authenticate(user=self.cliente_a)
        self.assertEqual(
            self.client.get("/api/carrito").json()["items"],
            [{"producto_id": "p1", "cantidad": 2}],
        )

    def test_si_catalogo_cae_el_carrito_sigue_guardado(self):
        self._poner("p1", 2)
        with patch("ordenes.views.obtener_producto",
                   side_effect=CatalogoNoDisponibleError("caído")):
            r = self.client.get("/api/carrito")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(LineaCarrito.objects.count(), 1)