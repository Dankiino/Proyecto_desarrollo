
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import MensajeContacto
from .serializers import MensajeContactoSerializer
from .permissions import EsAdminContacto


# Formulario público: recibir mensajes
class CrearMensajeContactoView(generics.CreateAPIView):
    queryset = MensajeContacto.objects.all()
    serializer_class = MensajeContactoSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"mensaje": "Tu mensaje fue enviado correctamente."},
            status=status.HTTP_201_CREATED,
        )


# Administrador autorizado: listar mensajes
class ListarMensajesContactoView(generics.ListAPIView):
    queryset = MensajeContacto.objects.all()
    serializer_class = MensajeContactoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [EsAdminContacto]


# Administrador autorizado: consultar un mensaje
class DetalleMensajeContactoView(generics.RetrieveAPIView):
    queryset = MensajeContacto.objects.all()
    serializer_class = MensajeContactoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [EsAdminContacto]
