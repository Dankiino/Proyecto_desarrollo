from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContenidoPagina, Tema
from .permissions import EsAdminContenidos
from .validaciones import validar_contenido


def serializar_tema(tema):
    if tema is None:
        return None
    return {
        "id": tema.id,
        "nombre": tema.nombre,
        "color_primario": tema.color_primario,
        "color_secundario": tema.color_secundario,
        "color_fondo": tema.color_fondo,
        "color_texto": tema.color_texto,
        "color_acento": tema.color_acento,
        "activo": tema.activo,
    }


def serializar_contenido(c):
    return {
        "pagina": c.pagina,
        "clave": c.clave,
        "tipo": c.tipo,
        "valor": c.valor,
        "texto_alternativo": c.texto_alternativo,
        "actualizado_en": c.actualizado_en,
        "actualizado_por": c.actualizado_por.correo if c.actualizado_por_id else None,
    }


def _datos_admin():
    contenidos = ContenidoPagina.objects.select_related("actualizado_por").order_by("pagina", "id")
    temas = Tema.objects.order_by("id")
    activo = next((t for t in temas if t.activo), None)
    return {
        "tema_activo": activo.id if activo else None,
        "temas": [serializar_tema(t) for t in temas],
        "contenidos": [serializar_contenido(c) for c in contenidos],
    }


class ContenidosPublicosView(APIView):
    """GET /api/contenidos — datos que muestran las páginas públicas (sin sesión)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        paginas = {}
        for c in ContenidoPagina.objects.order_by("pagina", "id"):
            paginas.setdefault(c.pagina, {})[c.clave] = {
                "tipo": c.tipo,
                "valor": c.valor,
                "texto_alternativo": c.texto_alternativo,
            }
        tema = Tema.objects.filter(activo=True).first()
        return Response({"tema": serializar_tema(tema), "paginas": paginas})


class ContenidosAdminView(APIView):
    """GET/PATCH /api/admin/contenidos — consulta y edición (solo administrador)."""

    permission_classes = [EsAdminContenidos]

    def get(self, request):
        return Response(_datos_admin())

    def patch(self, request):
        cambios = request.data.get("contenidos") if isinstance(request.data, dict) else None
        if not isinstance(cambios, list) or not cambios:
            return Response(
                {"detail": "Envía una lista no vacía en «contenidos»."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existentes = {(c.pagina, c.clave): c for c in ContenidoPagina.objects.all()}
        errores, validos = {}, []
        for item in cambios:
            if not isinstance(item, dict):
                return Response({"detail": "Cada cambio debe ser un objeto."}, status=status.HTTP_400_BAD_REQUEST)
            llave = (item.get("pagina"), item.get("clave"))
            nombre = f"{llave[0]}.{llave[1]}"
            contenido = existentes.get(llave)
            if contenido is None:
                errores[nombre] = {"clave": ["Este campo no es editable o no existe."]}
                continue
            limpios, errores_campo = validar_contenido(contenido, item)
            if errores_campo:
                errores[nombre] = errores_campo
            else:
                validos.append((contenido, limpios))

        # Si algún campo es inválido no se guarda nada: los valores válidos que ya
        # estaban en la base se conservan intactos.
        if errores:
            return Response(
                {"detail": "Revisa los campos marcados.", "campos": errores},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for contenido, limpios in validos:
                if (contenido.valor, contenido.texto_alternativo) == (limpios["valor"], limpios["texto_alternativo"]):
                    continue
                contenido.valor = limpios["valor"]
                contenido.texto_alternativo = limpios["texto_alternativo"]
                contenido.actualizado_por = request.user
                contenido.save(update_fields=["valor", "texto_alternativo", "actualizado_por", "actualizado_en"])

        return Response(_datos_admin())


class TemaActivoAdminView(APIView):
    """PUT /api/admin/tema-activo — elige uno de los temas aprobados (solo administrador)."""

    permission_classes = [EsAdminContenidos]

    def put(self, request):
        tema_id = request.data.get("tema_id") if isinstance(request.data, dict) else None
        if not isinstance(tema_id, str) or not tema_id:
            return Response({"campos": {"tema_id": ["Selecciona un tema."]}}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            tema = Tema.objects.select_for_update().filter(id=tema_id).first()
            if tema is None:
                return Response(
                    {"campos": {"tema_id": ["El tema no existe o no está aprobado."]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Tema.objects.exclude(id=tema.id).filter(activo=True).update(activo=False)
            if not tema.activo:
                tema.activo = True
                tema.save(update_fields=["activo"])

        return Response(serializar_tema(tema))
