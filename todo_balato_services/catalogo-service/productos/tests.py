from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import override_settings
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from rest_framework.test import APISimpleTestCase

from productos import mongo, repository

URI_FALSA = "mongodb://usuario:CLAVE_SECRETA@host-falso:27017/catalogo_db"


@override_settings(CATALOGO_MONGO_URI=URI_FALSA, CATALOGO_DB_NAME="catalogo_db")
class MongoHealthTests(APISimpleTestCase):
    def setUp(self):
        mongo.reset_client()
        self.addCleanup(mongo.reset_client)

    def _fake(self, mock_cls):
        db = mock_cls.return_value.__getitem__.return_value
        col = db.__getitem__.return_value
        return db, col

    @patch("productos.mongo.MongoClient")
    def test_lectura_ok(self, mock_cls):
        _, col = self._fake(mock_cls)
        col.find_one.return_value = {"_id": "x"}
        col.estimated_document_count.return_value = 3
        r = self.client.get("/api/health/mongo")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["mongo"]["productos"]["documentos"], 3)
        self.assertNotIn("CLAVE_SECRETA", r.content.decode())

    @patch("productos.mongo.MongoClient")
    def test_mongo_caido_devuelve_503(self, mock_cls):
        db, _ = self._fake(mock_cls)
        db.command.side_effect = ServerSelectionTimeoutError(f"fallo en {URI_FALSA}")
        r = self.client.get("/api/health/mongo")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["error"]["codigo"], "servicio_no_disponible")
        self.assertNotIn("CLAVE_SECRETA", r.content.decode())

    @patch("productos.mongo.MongoClient")
    def test_credenciales_rechazadas_devuelve_503(self, mock_cls):
        db, _ = self._fake(mock_cls)
        db.command.side_effect = OperationFailure("Authentication failed", 18)
        r = self.client.get("/api/health/mongo")
        self.assertEqual(r.status_code, 503)
        self.assertIn("rechazó", r.json()["error"]["mensaje"])

    @patch("productos.mongo.MongoClient")
    def test_coleccion_vacia_devuelve_503(self, mock_cls):
        _, col = self._fake(mock_cls)
        col.find_one.return_value = None
        col.estimated_document_count.return_value = 0
        r = self.client.get("/api/health/mongo")
        self.assertEqual(r.status_code, 503)

    @override_settings(CATALOGO_MONGO_URI="")
    def test_sin_uri_devuelve_503(self):
        r = self.client.get("/api/health/mongo")
        self.assertEqual(r.status_code, 503)
        self.assertIn("no está configurada", r.json()["error"]["mensaje"])

    def test_health_simple_no_necesita_mongo(self):
        with override_settings(CATALOGO_MONGO_URI=""):
            self.assertEqual(self.client.get("/api/health").status_code, 200)


class CatalogoAPITests(APISimpleTestCase):
    @patch("productos.views.repository.listar_categorias")
    def test_lista_categorias_publicas(self, listar_categorias):
        listar_categorias.return_value = [
            {"_id": "cocina", "nombre": "Cocina", "activa": True}
        ]

        respuesta = self.client.get("/api/categorias")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json(),
            {"results": [{"id": "cocina", "nombre": "Cocina"}]},
        )

    @patch("productos.views.repository.listar_categorias")
    @patch("productos.views.repository.listar_productos")
    def test_lista_productos_formatea_documentos_mongo(
        self, listar_productos, listar_categorias
    ):
        listar_categorias.return_value = [{"_id": "cocina", "nombre": "Cocina"}]
        listar_productos.return_value = (
            [
                {
                    "_id": "prod_0001",
                    "nombre": "Vasos",
                    "precio": 3990,
                    "stock_fisico": 10,
                    "stock_reservado": 3,
                    "categoria_id": "cocina",
                    "imagenes": [{"url": "/vasos.jpg", "alt": "Vasos"}],
                    "activo": True,
                }
            ],
            1,
        )

        respuesta = self.client.get("/api/productos?page=1&page_size=50")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["count"], 1)
        self.assertEqual(
            respuesta.json()["results"][0],
            {
                "id": "prod_0001",
                "nombre": "Vasos",
                "precio": 3990,
                "moneda": "CLP",
                "disponible": True,
                "categorias": [{"id": "cocina", "nombre": "Cocina"}],
                "imagen_principal": {
                    "url": "/vasos.jpg",
                    "texto_alternativo": "Vasos",
                },
            },
        )
        listar_productos.assert_called_once_with(
            categoria_id=None,
            precio_min=None,
            precio_max=None,
            disponible=False,
            pagina=1,
            tamano=50,
            orden="recientes",
        )

    @patch("productos.views.repository.listar_categorias")
    @patch("productos.views.repository.obtener_producto")
    def test_detalle_producto_y_producto_inexistente(
        self, obtener_producto, listar_categorias
    ):
        listar_categorias.return_value = []
        obtener_producto.return_value = {
            "_id": "prod_0001",
            "nombre": "Vasos",
            "stock_fisico": 10,
            "stock_reservado": 3,
            "actualizado_en": datetime(2026, 10, 12, 14, 0),
        }

        detalle = self.client.get("/api/productos/prod_0001")

        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()["stock_disponible"], 7)
        obtener_producto.return_value = None

        inexistente = self.client.get("/api/productos/no-existe")

        self.assertEqual(inexistente.status_code, 404)
        self.assertEqual(inexistente.json()["error"]["codigo"], "no_encontrado")

    def test_parametros_invalidos_responden_error_de_validacion(self):
        respuesta = self.client.get("/api/productos?page_size=51")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json()["error"]["campos"]["page_size"],
            ["Debe ser un entero entre 1 y 50."],
        )

    @patch("productos.views.repository.listar_categorias")
    @patch("productos.views.repository.listar_productos")
    def test_producto_sin_imagen_incluye_imagen_principal_nula(
        self, listar_productos, listar_categorias
    ):
        listar_categorias.return_value = []
        listar_productos.return_value = (
            [{"_id": "prod_sin_imagen", "nombre": "Producto", "imagenes": []}],
            1,
        )

        respuesta = self.client.get("/api/productos")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.json()["results"][0]["imagen_principal"])


class ActiveProductRepositoryTests(APISimpleTestCase):
    @patch("productos.repository.get_productos")
    def test_listado_consulta_solo_productos_activos(self, get_productos):
        coleccion = get_productos.return_value
        cursor = MagicMock()
        cursor.sort.return_value = cursor
        cursor.skip.return_value = cursor
        cursor.limit.return_value = []
        coleccion.find.return_value = cursor

        repository.listar_productos()

        filtro_activos = {"activo": True}
        coleccion.count_documents.assert_called_once_with(filtro_activos)
        coleccion.find.assert_called_once_with(filtro_activos)

    @patch("productos.repository.get_productos")
    def test_detalle_busca_solo_productos_activos(self, get_productos):
        repository.obtener_producto("prod_0001")

        get_productos.return_value.find_one.assert_called_once_with(
            {"_id": "prod_0001", "activo": True}
        )