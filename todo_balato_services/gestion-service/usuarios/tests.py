import re
from datetime import timedelta

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import TokenCuenta, Usuario

CLAVE = "Clave-Segura-2026!x"
CLAVE_NUEVA = "Otra-Clave-Segura-2027!y"


def crear_usuario(correo="ana@example.com", estado="ACTIVO", rol="CLIENTE", password=CLAVE):
    return Usuario.objects.create_user(
        correo=correo, password=password, nombre="Ana", apellido="Perez", rol=rol, estado=estado)


class FlujoCuentaTestCase(TestCase):
    def setUp(self):
        cache.clear()  # los contadores de límite de solicitudes no deben pasar de una prueba a otra
        self.api = APIClient()

    def token_enviado(self):
        """Token del último correo enviado (el enlace es lo único que lo contiene)."""
        return re.search(r"token=([\w-]+)", mail.outbox[-1].body).group(1)

    def registrar(self, correo="ana@example.com", password=CLAVE):
        return self.api.post("/api/registro", {
            "nombre": "Ana", "apellido": "Perez", "correo": correo, "password": password}, format="json")

    def activar(self, token):
        return self.api.post("/api/activar", {"token": token}, format="json")

    def solicitar_recuperacion(self, correo):
        return self.api.post("/api/recuperar-password", {"correo": correo}, format="json")

    def restablecer(self, token, password=CLAVE_NUEVA):
        return self.api.post("/api/restablecer-password", {"token": token, "password": password}, format="json")

    def login(self, correo="ana@example.com", password=CLAVE):
        return self.api.post("/api/login", {"correo": correo, "password": password}, format="json")


class ActivacionTests(FlujoCuentaTestCase):
    def test_registro_crea_cuenta_pendiente_y_envia_enlace(self):
        r = self.registrar()
        self.assertEqual(r.status_code, 201)
        u = Usuario.objects.get(correo="ana@example.com")
        self.assertEqual((u.estado, u.rol), ("PENDIENTE", "CLIENTE"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@example.com"])
        self.assertNotIn(CLAVE, mail.outbox[0].body)

    def test_solo_se_guarda_el_hash_del_token_y_de_la_clave(self):
        self.registrar()
        token = self.token_enviado()
        t = TokenCuenta.objects.get()
        self.assertNotEqual(t.token_hash, token)
        self.assertNotIn(token, t.token_hash)
        self.assertNotEqual(Usuario.objects.get().password, CLAVE)

    def test_registro_ignora_rol_y_rechaza_clave_debil(self):
        r = self.api.post("/api/registro", {
            "nombre": "Ana", "apellido": "Perez", "correo": "ana@example.com",
            "password": CLAVE, "rol": "ADMIN", "estado": "ACTIVO"}, format="json")
        self.assertEqual((r.status_code, Usuario.objects.get().rol, Usuario.objects.get().estado), (201, "CLIENTE", "PENDIENTE"))
        r = self.registrar(correo="otra@example.com", password="12345678")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)
        self.assertFalse(Usuario.objects.filter(correo="otra@example.com").exists())

    def test_cuenta_pendiente_no_inicia_sesion(self):
        self.registrar()
        r = self.login()
        self.assertEqual(r.status_code, 403)
        self.assertNotIn("access", r.data)

    def test_activacion_valida_habilita_el_login(self):
        self.registrar()
        r = self.activar(self.token_enviado())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.get().estado, "ACTIVO")
        self.assertEqual(self.login().status_code, 200)

    def test_enlace_repetido_alterado_o_vencido_se_rechaza(self):
        self.registrar()
        token = self.token_enviado()
        alterado = token[:-1] + ("A" if token[-1] != "A" else "B")
        self.assertEqual(self.activar(alterado).status_code, 400)
        self.assertEqual(self.activar("inventado").status_code, 400)
        TokenCuenta.objects.update(vence_en=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.activar(token).status_code, 400)
        self.assertEqual(Usuario.objects.get().estado, "PENDIENTE")
        TokenCuenta.objects.update(vence_en=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.activar(token).status_code, 200)
        self.assertEqual(self.activar(token).status_code, 400)  # repetido

    def test_enlace_de_cuenta_bloqueada_no_la_activa(self):
        self.registrar()
        token = self.token_enviado()
        Usuario.objects.update(estado="BLOQUEADO")
        self.assertEqual(self.activar(token).status_code, 400)
        self.assertEqual(Usuario.objects.get().estado, "BLOQUEADO")

    def test_reenvio_invalida_el_enlace_anterior(self):
        self.registrar()
        viejo = self.token_enviado()
        r = self.api.post("/api/activar/reenviar", {"correo": "ana@example.com"}, format="json")
        self.assertEqual((r.status_code, len(mail.outbox)), (200, 2))
        self.assertEqual(self.activar(viejo).status_code, 400)
        self.assertEqual(self.activar(self.token_enviado()).status_code, 200)

    def test_reenvio_responde_igual_para_correo_no_registrado_o_no_pendiente(self):
        crear_usuario("activa@example.com")
        crear_usuario("bloq@example.com", estado="BLOQUEADO")
        respuestas = []
        for correo in ("noexiste@example.com", "activa@example.com", "bloq@example.com"):
            r = self.api.post("/api/activar/reenviar", {"correo": correo}, format="json")
            respuestas.append((r.status_code, r.data))
        self.assertEqual(len(set(str(x) for x in respuestas)), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_fallo_de_correo_no_impide_el_registro(self):
        with self.settings(MAILERS={"default": {"BACKEND": "usuarios.tests.CorreoQueFalla"}}):
            self.assertEqual(self.registrar().status_code, 201)
        self.assertEqual(Usuario.objects.get().estado, "PENDIENTE")


class RecuperacionTests(FlujoCuentaTestCase):
    def test_limite_de_solicitudes_en_recuperacion_y_reenvio(self):
        crear_usuario()
        for _ in range(5):
            self.assertEqual(self.solicitar_recuperacion("ana@example.com").status_code, 200)
        self.assertEqual(self.solicitar_recuperacion("ana@example.com").status_code, 429)
        self.assertEqual(len(mail.outbox), 5)  # la sexta no envió correo
        for _ in range(5):
            r = self.api.post("/api/activar/reenviar", {"correo": "ana@example.com"}, format="json")
            self.assertEqual(r.status_code, 200)
        r = self.api.post("/api/activar/reenviar", {"correo": "ana@example.com"}, format="json")
        self.assertEqual(r.status_code, 429)

    def test_clave_demasiado_larga_se_rechaza_sin_consumir_el_enlace(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        token = self.token_enviado()
        r = self.restablecer(token, "Aa1!" * 100)
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)
        self.assertEqual(self.registrar(correo="otra@example.com", password="Aa1!" * 100).status_code, 400)
        self.assertEqual(self.restablecer(token).status_code, 200)  # el enlace seguía sirviendo

    def test_respuesta_identica_exista_o_no_el_correo(self):
        crear_usuario("ana@example.com")
        crear_usuario("pend@example.com", estado="PENDIENTE")
        crear_usuario("bloq@example.com", estado="BLOQUEADO")
        respuestas = []
        for correo in ("ana@example.com", "noexiste@example.com", "pend@example.com", "bloq@example.com"):
            r = self.solicitar_recuperacion(correo)
            respuestas.append((r.status_code, r.data))
        self.assertEqual(len(set(str(x) for x in respuestas)), 1)
        self.assertEqual([m.to for m in mail.outbox], [["ana@example.com"]])  # solo la cuenta activa

    def test_correo_con_formato_invalido_es_error_de_validacion(self):
        self.assertEqual(self.solicitar_recuperacion("no-es-correo").status_code, 400)

    def test_restablecer_con_enlace_valido(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        r = self.restablecer(self.token_enviado())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.login(password=CLAVE).status_code, 401)
        self.assertEqual(self.login(password=CLAVE_NUEVA).status_code, 200)
        self.assertNotEqual(Usuario.objects.get().password, CLAVE_NUEVA)  # solo el hash

    def test_enlace_repetido_alterado_o_vencido_se_rechaza(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        token = self.token_enviado()
        alterado = "x" + token[1:]
        self.assertEqual(self.restablecer(alterado).status_code, 400)
        TokenCuenta.objects.update(vence_en=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.restablecer(token).status_code, 400)
        TokenCuenta.objects.update(vence_en=timezone.now() + timedelta(minutes=5))
        self.assertEqual(self.restablecer(token).status_code, 200)
        self.assertEqual(self.restablecer(token, "Tercera-Clave-2028!z").status_code, 400)  # repetido
        self.assertEqual(self.login(password=CLAVE_NUEVA).status_code, 200)

    def test_clave_invalida_no_consume_el_enlace(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        token = self.token_enviado()
        for debil in ("12345678", "corta", "password", "ana@example.com"):
            r = self.restablecer(token, debil)
            self.assertEqual(r.status_code, 400)
            self.assertIn("password", r.data)
        self.assertEqual(self.login(password=CLAVE).status_code, 200)  # clave intacta
        self.assertEqual(self.restablecer(token).status_code, 200)     # el enlace seguía sirviendo

    def test_enlace_de_otro_proposito_no_sirve(self):
        self.registrar()
        self.assertEqual(self.restablecer(self.token_enviado()).status_code, 400)  # token de activación

    def test_cuenta_bloqueada_no_restablece(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        token = self.token_enviado()
        Usuario.objects.update(estado="BLOQUEADO")
        self.assertEqual(self.restablecer(token).status_code, 400)
        self.assertEqual(self.login(password=CLAVE).status_code, 403)
        self.assertEqual(self.login(password=CLAVE_NUEVA).status_code, 401)

    def test_nuevo_enlace_invalida_el_anterior(self):
        crear_usuario()
        self.solicitar_recuperacion("ana@example.com")
        viejo = self.token_enviado()
        self.solicitar_recuperacion("ana@example.com")
        self.assertEqual(self.restablecer(viejo).status_code, 400)
        self.assertEqual(self.restablecer(self.token_enviado()).status_code, 200)

    def test_restablecer_cierra_las_sesiones_existentes(self):
        crear_usuario()
        refresh = self.login().data["refresh"]
        self.solicitar_recuperacion("ana@example.com")
        self.restablecer(self.token_enviado())
        with self.assertRaises(TokenError):  # el refresh anterior quedó en la lista negra
            RefreshToken(refresh)


class BloqueoTests(FlujoCuentaTestCase):
    def test_bloqueado_no_inicia_sesion(self):
        crear_usuario(estado="BLOQUEADO")
        r = self.login()
        self.assertEqual(r.status_code, 403)
        self.assertNotIn("access", r.data)

    def test_token_obtenido_antes_del_bloqueo_deja_de_servir(self):
        crear_usuario()
        crear_usuario("admin@example.com", rol="ADMIN")
        sesion = self.login().data
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {sesion['access']}")
        self.assertEqual(cliente.get("/api/usuarios/me").status_code, 200)

        admin = APIClient()
        admin.credentials(HTTP_AUTHORIZATION="Bearer " + self.login("admin@example.com").data["access"])
        r = admin.post(f"/api/usuarios/{Usuario.objects.get(correo='ana@example.com').id}/bloquear")
        self.assertEqual(r.status_code, 200)

        self.assertEqual(cliente.get("/api/usuarios/me").status_code, 401)  # mismo access de antes
        with self.assertRaises(TokenError):
            RefreshToken(sesion["refresh"])

        admin.post(f"/api/usuarios/{Usuario.objects.get(correo='ana@example.com').id}/desbloquear")
        self.assertEqual(cliente.get("/api/usuarios/me").status_code, 200)


class CorreoQueFalla:
    """Backend de correo que siempre falla, para probar que no rompe la operación."""
    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, mensajes):
        raise ConnectionError("SMTP caído")
