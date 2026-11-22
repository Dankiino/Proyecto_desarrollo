from unittest.mock import patch

from django.test import override_settings
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from rest_framework.test import APISimpleTestCase

from productos import mongo

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