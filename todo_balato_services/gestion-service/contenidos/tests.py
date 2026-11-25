from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from usuarios.models import Usuario

from .models import ContenidoPagina, Tema

CLAVE = "Clave-Segura-2026!x"


def crear_usuario(correo, rol="ADMIN", estado="ACTIVO"):
    return Usuario.objects.create_user(
        correo=correo, password=CLAVE, nombre="Ana", apellido="Perez", rol=rol, estado=estado)


class CargaInicialTests(TestCase):
    def test_carga_es_idempotente_y_no_sobrescribe(self):
        call_command("cargar_datos_iniciales", verbosity=0)
        self.assertEqual(Tema.objects.count(), 4)
        self.assertEqual(Tema.objects.filter(activo=True).count(), 1)
        total = ContenidoPagina.objects.count()

        ContenidoPagina.objects.filter(pagina="inicio", clave="titulo").update(valor="Editado")
        Tema.objects.filter(activo=True).update(activo=False)
        Tema.objects.filter(id="balato-oscuro").update(activo=True, nombre="Mi tema")

        call_command("cargar_datos_iniciales", verbosity=0)
        self.assertEqual(Tema.objects.count(), 4)
        self.assertEqual(ContenidoPagina.objects.count(), total)
        self.assertEqual(ContenidoPagina.objects.get(pagina="inicio", clave="titulo").valor, "Editado")
        self.assertEqual(list(Tema.objects.filter(activo=True).values_list("id", "nombre")), [("balato-oscuro", "Mi tema")])


class ContenidosApiTests(TestCase):
    def setUp(self):
        call_command("cargar_datos_iniciales", verbosity=0)
        self.api = APIClient()
        self.admin = crear_usuario("admin@example.com")

    def autenticar(self, usuario):
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuario)}")

    def patch(self, contenidos):
        return self.api.patch("/api/admin/contenidos", {"contenidos": contenidos}, format="json")

    # --- Lectura pública ---
    def test_publico_devuelve_paginas_y_tema_sin_sesion(self):
        r = self.api.get("/api/contenidos")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["tema"]["id"], "balato-clasico")
        self.assertEqual(set(r.data["paginas"]), {"inicio", "contacto", "quienes-somos"})
        self.assertEqual(r.data["paginas"]["inicio"]["titulo"]["valor"], "Bienvenido a Todo Balato")

    def test_publico_ignora_token_invalido(self):
        self.api.credentials(HTTP_AUTHORIZATION="Bearer basura")
        self.assertEqual(self.api.get("/api/contenidos").status_code, 200)

    # --- Autorización ---
    def test_sin_sesion_no_puede_editar(self):
        self.assertEqual(self.api.get("/api/admin/contenidos").status_code, 401)
        r = self.patch([{"pagina": "inicio", "clave": "titulo", "valor": "Hack"}])
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.api.put("/api/admin/tema-activo", {"tema_id": "balato-oscuro"}, format="json").status_code, 401)
        self.assertEqual(ContenidoPagina.objects.get(pagina="inicio", clave="titulo").valor, "Bienvenido a Todo Balato")

    def test_cliente_no_puede_editar(self):
        self.autenticar(crear_usuario("cliente@example.com", rol="CLIENTE"))
        self.assertEqual(self.api.get("/api/admin/contenidos").status_code, 403)
        self.assertEqual(self.patch([{"pagina": "inicio", "clave": "titulo", "valor": "Hack"}]).status_code, 403)
        self.assertEqual(self.api.put("/api/admin/tema-activo", {"tema_id": "balato-oscuro"}, format="json").status_code, 403)

    def test_admin_bloqueado_no_puede_editar(self):
        bloqueado = crear_usuario("bloq@example.com")
        self.autenticar(bloqueado)
        bloqueado.estado = "BLOQUEADO"
        bloqueado.save()
        self.assertIn(self.api.get("/api/admin/contenidos").status_code, (401, 403))

    def test_sesion_vencida_no_puede_editar(self):
        token = AccessToken.for_user(self.admin)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.api.get("/api/admin/contenidos").status_code, 401)

    # --- Edición ---
    def test_admin_edita_y_lo_ve_el_publico(self):
        self.autenticar(self.admin)
        r = self.patch([
            {"pagina": "inicio", "clave": "titulo", "valor": "  Nuevo título  "},
            {"pagina": "inicio", "clave": "banner_principal", "valor": "https://cdn.example.com/b.png",
             "texto_alternativo": "Banner"},
            {"pagina": "inicio", "clave": "banner_enlace", "valor": "/catalogo?cat=hogar"},
        ])
        self.assertEqual(r.status_code, 200, r.data)
        c = ContenidoPagina.objects.get(pagina="inicio", clave="titulo")
        self.assertEqual((c.valor, c.actualizado_por), ("Nuevo título", self.admin))
        publico = self.api.get("/api/contenidos").data["paginas"]["inicio"]
        self.assertEqual(publico["titulo"]["valor"], "Nuevo título")
        self.assertEqual(publico["banner_principal"]["valor"], "https://cdn.example.com/b.png")

    def test_errores_por_campo_no_reemplazan_valores_validos(self):
        self.autenticar(self.admin)
        r = self.patch([
            {"pagina": "inicio", "clave": "titulo", "valor": "Título válido"},
            {"pagina": "inicio", "clave": "eslogan", "valor": "   "},
            {"pagina": "inicio", "clave": "banner_principal", "valor": "javascript:alert(1)", "texto_alternativo": ""},
            {"pagina": "contacto", "clave": "correo", "valor": "no-es-correo"},
            {"pagina": "inicio", "clave": "inventada", "valor": "x"},
        ])
        self.assertEqual(r.status_code, 400)
        campos = r.data["campos"]
        self.assertIn("valor", campos["inicio.eslogan"])
        self.assertIn("valor", campos["inicio.banner_principal"])
        self.assertIn("texto_alternativo", campos["inicio.banner_principal"])
        self.assertIn("valor", campos["contacto.correo"])
        self.assertIn("clave", campos["inicio.inventada"])
        self.assertNotIn("inicio.titulo", campos)
        # Nada se guardó: ni siquiera el campo válido.
        self.assertEqual(ContenidoPagina.objects.get(pagina="inicio", clave="titulo").valor, "Bienvenido a Todo Balato")
        self.assertEqual(ContenidoPagina.objects.get(pagina="inicio", clave="eslogan").valor, "Bueno, bonito y balato.")

    def test_cuerpo_invalido(self):
        self.autenticar(self.admin)
        self.assertEqual(self.patch([]).status_code, 400)
        self.assertEqual(self.api.patch("/api/admin/contenidos", {"x": 1}, format="json").status_code, 400)

    # --- Tema ---
    def test_admin_cambia_tema_activo(self):
        self.autenticar(self.admin)
        r = self.api.put("/api/admin/tema-activo", {"tema_id": "balato-oscuro"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(Tema.objects.filter(activo=True).values_list("id", flat=True)), ["balato-oscuro"])
        self.assertEqual(self.api.get("/api/contenidos").data["tema"]["id"], "balato-oscuro")

    def test_tema_inexistente_no_cambia_nada(self):
        self.autenticar(self.admin)
        r = self.api.put("/api/admin/tema-activo", {"tema_id": "rosado"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("tema_id", r.data["campos"])
        self.assertEqual(list(Tema.objects.filter(activo=True).values_list("id", flat=True)), ["balato-clasico"])
