from django.core.management import call_command
from django.test import TestCase

from .models import ContenidoPagina, Tema


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
