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
            buscar="",
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
class AjusteInventarioSerializerTests(APISimpleTestCase):

    def validar(self, datos):
        from productos.serializers import AjusteInventarioSerializer

        serializer = AjusteInventarioSerializer(data=datos)
        return serializer.is_valid()

    def test_stock_entero_positivo(self):
        self.assertTrue(self.validar({
            "stock_fisico": 70,
            "motivo": "Conteo físico",
        }))

    def test_stock_cero(self):
        self.assertTrue(self.validar({
            "stock_fisico": 0,
            "motivo": "Sin existencias",
        }))

    def test_cantidades_invalidas(self):
        for cantidad in [-1, 2.5, "10", True, None, 2147483648]:
            with self.subTest(cantidad=cantidad):
                self.assertFalse(self.validar({
                    "stock_fisico": cantidad,
                    "motivo": "Prueba",
                }))

    def test_motivo_vacio(self):
        for motivo in ["", "   "]:
            with self.subTest(motivo=motivo):
                self.assertFalse(self.validar({
                    "stock_fisico": 10,
                    "motivo": motivo,
                }))

    def test_motivo_demasiado_largo(self):
        self.assertFalse(self.validar({
            "stock_fisico": 10,
            "motivo": "a" * 501,
        }))

    def test_campos_protegidos(self):
        for campo in [
            "stock_reservado",
            "historial_ajustes",
            "administrador_id",
            "administrador_nombre",
            "administrador_correo",
            "fecha",
        ]:
            with self.subTest(campo=campo):
                self.assertFalse(self.validar({
                    "stock_fisico": 10,
                    "motivo": "Prueba",
                    campo: "valor no autorizado",
                }))

class AjusteInventarioPermisosTests(APISimpleTestCase):

    ruta = "/api/admin/productos/prod_0001/ajustes"

    @patch("productos.repository.get_productos")
    def test_sin_token(self, get_productos):
        respuesta = self.client.post(
            self.ruta,
            {"stock_fisico": 20, "motivo": "Prueba"},
            format="json",
        )

        self.assertIn(respuesta.status_code, [401, 403])
        get_productos.assert_not_called()

    @patch("productos.repository.get_productos")
    @patch("productos.admin_auth.json.load")
    @patch("productos.admin_auth.urllib.request.urlopen")
    def test_cuentas_no_autorizadas(
        self, urlopen, cargar_json, get_productos
    ):
        for rol, estado in [
            ("CLIENTE", "ACTIVO"),
            ("ADMIN", "BLOQUEADO"),
            ("ADMIN", "PENDIENTE"),
        ]:
            with self.subTest(rol=rol, estado=estado):
                cargar_json.return_value = {
                    "id": 1,
                    "rol": rol,
                    "estado": estado,
                }

                for metodo in ["get", "post"]:
                    respuesta = getattr(self.client, metodo)(
                        self.ruta,
                        {"stock_fisico": 20, "motivo": "Prueba"},
                        format="json",
                        HTTP_AUTHORIZATION="Bearer token-prueba",
                    )

                    self.assertEqual(respuesta.status_code, 403)

        get_productos.assert_not_called()

class AjusteInventarioOperacionTests(APISimpleTestCase):

    ruta = "/api/admin/productos/prod_0001/ajustes"

    administrador = {
        "id": 1,
        "nombre": "Admin",
        "apellido": "Prueba",
        "correo": "admin@example.com",
        "rol": "ADMIN",
        "estado": "ACTIVO",
    }

    @patch("productos.views.repository.ajustar_inventario")
    @patch("productos.views.verificar_admin")
    def test_ajuste_valido(self, verificar_admin, ajustar):
        verificar_admin.return_value = self.administrador

        ajustar.return_value = {
            "stock_fisico": 70,
            "stock_reservado": 5,
            "historial_ajustes": [{
                "ajuste_id": "ajuste_001",
                "producto_id": "prod_0001",
                "stock_anterior": 50,
                "stock_nuevo": 70,
                "motivo": "Conteo físico",
                "administrador_id": 1,
                "administrador_nombre": "Admin Prueba",
                "administrador_correo": "admin@example.com",
                "fecha": datetime(2026, 11, 24, 18, 0),
            }],
        }

        respuesta = self.client.post(
            self.ruta,
            {
                "stock_fisico": 70,
                "motivo": "Conteo físico",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["stock_fisico"], 70)
        self.assertEqual(
            respuesta.json()["ajuste"]["administrador_nombre"],
            "Admin Prueba",
        )

        ajustar.assert_called_once_with(
            producto_id="prod_0001",
            stock_nuevo=70,
            motivo="Conteo físico",
            administrador=self.administrador,
        )

    @patch("productos.views.repository.obtener_producto")
    @patch("productos.views.repository.ajustar_inventario")
    @patch("productos.views.verificar_admin")
    def test_stock_inferior_al_reservado(
        self, verificar_admin, ajustar, obtener
    ):
        verificar_admin.return_value = self.administrador
        ajustar.return_value = None

        obtener.return_value = {
            "_id": "prod_0001",
            "stock_fisico": 50,
            "stock_reservado": 10,
        }

        respuesta = self.client.post(
            self.ruta,
            {
                "stock_fisico": 5,
                "motivo": "Corrección de inventario",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(
            respuesta.json()["stock_reservado"], 10
        )
class AjusteInventarioHistorialTests(APISimpleTestCase):

    ruta = "/api/admin/productos/prod_0001/ajustes"

    @patch("productos.views.repository.obtener_producto")
    @patch("productos.views.verificar_admin")
    def test_consultar_historial(self, verificar_admin, obtener):
        verificar_admin.return_value = {
            "id": 1,
            "rol": "ADMIN",
            "estado": "ACTIVO",
        }

        obtener.return_value = {
            "_id": "prod_0001",
            "stock_fisico": 70,
            "stock_reservado": 5,
            "historial_ajustes": [
                {
                    "ajuste_id": "ajuste_001",
                    "stock_anterior": 40,
                    "stock_nuevo": 50,
                },
                {
                    "ajuste_id": "ajuste_002",
                    "stock_anterior": 50,
                    "stock_nuevo": 70,
                },
            ],
        }

        respuesta = self.client.get(self.ruta)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["total"], 2)
        self.assertEqual(respuesta.json()["stock_fisico"], 70)
        self.assertEqual(
            respuesta.json()["historial"][0]["ajuste_id"],
            "ajuste_002",
        )

    @patch("productos.views.repository.obtener_producto")
    @patch("productos.views.verificar_admin")
    def test_historial_vacio(self, verificar_admin, obtener):
        verificar_admin.return_value = {
            "rol": "ADMIN",
            "estado": "ACTIVO",
        }

        obtener.return_value = {
            "_id": "prod_0001",
            "stock_fisico": 50,
            "stock_reservado": 0,
        }

        respuesta = self.client.get(self.ruta)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["total"], 0)
        self.assertEqual(respuesta.json()["historial"], [])

class InventarioCamposProtegidosTests(APISimpleTestCase):

    ruta = "/api/admin/productos/prod_0001"

    @patch("productos.views.repository.actualizar_producto")
    @patch("productos.views.repository.obtener_producto")
    @patch("productos.views.verificar_admin")
    def test_edicion_general_rechaza_campos_protegidos(
        self, verificar_admin, obtener, actualizar
    ):
        verificar_admin.return_value = {
            "id": 1,
            "rol": "ADMIN",
            "estado": "ACTIVO",
        }

        obtener.return_value = {
            "_id": "prod_0001",
            "nombre": "Producto de prueba",
            "descripcion": "Descripción de prueba",
            "precio": 5000,
            "stock_fisico": 50,
            "stock_reservado": 10,
            "categoria_id": "cocina",
            "imagenes": [],
            "activo": True,
        }

        campos = {
            "stock_fisico": 100,
            "stock_reservado": 0,
            "historial_ajustes": [],
        }

        for campo, valor in campos.items():
            with self.subTest(campo=campo):
                respuesta = self.client.patch(
                    self.ruta,
                    {campo: valor},
                    format="json",
                )

                self.assertEqual(respuesta.status_code, 400)

        actualizar.assert_not_called()

class AjusteInventarioRepositoryTests(APISimpleTestCase):

    @patch("productos.repository.get_productos")
    def test_actualizacion_atomica(self, get_productos):
        coleccion = get_productos.return_value

        administrador = {
            "id": 1,
            "nombre": "Admin",
            "apellido": "Prueba",
            "correo": "admin@example.com",
        }

        repository.ajustar_inventario(
            producto_id="prod_0001",
            stock_nuevo=70,
            motivo="Conteo físico",
            administrador=administrador,
        )

        coleccion.find_one_and_update.assert_called_once()

        argumentos = coleccion.find_one_and_update.call_args.args

        filtro = argumentos[0]
        pipeline = argumentos[1]

        self.assertEqual(filtro["_id"], "prod_0001")
        self.assertEqual(
            filtro["stock_reservado"],
            {"$lte": 70},
        )

        cambios = pipeline[0]["$set"]

        self.assertEqual(cambios["stock_fisico"], 70)
        self.assertNotIn("stock_reservado", cambios)

        ajuste = cambios["historial_ajustes"][
            "$concatArrays"
        ][1][0]

        self.assertEqual(ajuste["stock_anterior"], "$stock_fisico")
        self.assertEqual(ajuste["stock_nuevo"], 70)
        self.assertEqual(ajuste["administrador_id"], 1)
        self.assertEqual(
            ajuste["administrador_nombre"],
            {"$literal": "Admin Prueba"},
        )
        self.assertEqual(
            ajuste["motivo"],
            {"$literal": "Conteo físico"},
        )
        self.assertIn("fecha", ajuste)
