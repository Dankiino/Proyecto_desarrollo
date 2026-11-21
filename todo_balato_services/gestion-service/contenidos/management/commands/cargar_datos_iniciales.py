from django.core.management.base import BaseCommand
from django.db import transaction

from contenidos.datos_iniciales import CONTENIDOS, TEMA_ACTIVO_POR_DEFECTO, TEMAS
from contenidos.models import ContenidoPagina, Tema


class Command(BaseCommand):
    help = "Carga temas y contenidos iniciales en PostgreSQL de Gestión (idempotente, no sobrescribe)."

    @transaction.atomic
    def handle(self, *args, **options):
        temas = contenidos = 0
        for id_, nombre, primario, secundario, fondo, texto, acento in TEMAS:
            _, creado = Tema.objects.get_or_create(
                id=id_,
                defaults=dict(
                    nombre=nombre, color_primario=primario, color_secundario=secundario,
                    color_fondo=fondo, color_texto=texto, color_acento=acento,
                    activo=id_ == TEMA_ACTIVO_POR_DEFECTO and not Tema.objects.filter(activo=True).exists(),
                ),
            )
            temas += creado
        for pagina, clave, tipo, valor, alt in CONTENIDOS:
            _, creado = ContenidoPagina.objects.get_or_create(
                pagina=pagina, clave=clave,
                defaults=dict(tipo=tipo, valor=valor, texto_alternativo=alt),
            )
            contenidos += creado
        self.stdout.write(
            f"Temas: {temas} creados, {len(TEMAS) - temas} ya existían. "
            f"Contenidos: {contenidos} creados, {len(CONTENIDOS) - contenidos} ya existían."
        )
