from rest_framework.response import Response
from rest_framework.views import APIView

from .repository import comprobar_lectura


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "catalogo-service"})


class MongoHealthView(APIView):
    def get(self, request):
        colecciones = comprobar_lectura()  # lanza CatalogoDBError -> 503
        return Response(
            {"status": "ok", "service": "catalogo-service", "mongo": colecciones}
        )