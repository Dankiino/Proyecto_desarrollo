from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone

from .models import TokenCuenta, Usuario
from .serializers import (
    CorreoSerializer, RegistroSerializer, RestablecerPasswordSerializer,
    TokenSerializer, UsuarioSerializer, validar_password,
)
from .permissions import EsAdminActivo
from .servicios import consumir_token, enviar_enlace, revocar_sesiones

# Misma respuesta exista o no el correo, para no revelar qué correos están registrados.
RESPUESTA_GENERICA = {"detail": "Si el correo corresponde a una cuenta elegible, enviaremos un enlace."}
ENLACE_INVALIDO = {"detail": "El enlace es inválido, venció o ya fue usado."}


class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        enviar_enlace(serializer.save(), "ACTIVACION")


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        correo = request.data.get("correo")
        password = request.data.get("password")
        usuario = authenticate(request, correo=correo, password=password)

        if usuario is None:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        if usuario.estado != "ACTIVO":
            return Response({"detail": "Cuenta no activa"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(usuario)
        refresh["rol"] = usuario.rol
        refresh["estado"] = usuario.estado
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "rol": usuario.rol,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class UsuarioListView(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdminActivo]


class BloquearUsuarioView(APIView):
    permission_classes = [EsAdminActivo]

    def post(self, request, pk):
        if str(request.user.id) == str(pk):
            return Response({"detail": "No puedes bloquearte a ti mismo"}, status=400)

        try:
            objetivo = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({"detail": "Usuario no encontrado"}, status=404)

        if objetivo.rol == "ADMIN":
            admins_activos = Usuario.objects.filter(rol="ADMIN", estado="ACTIVO").exclude(pk=pk).count()
            if admins_activos == 0:
                return Response({"detail": "No se puede bloquear al último administrador activo"}, status=400)

        objetivo.estado = "BLOQUEADO"
        objetivo.save()
        revocar_sesiones(objetivo)
        return Response(UsuarioSerializer(objetivo).data)


class DesbloquearUsuarioView(APIView):
    permission_classes = [EsAdminActivo]

    def post(self, request, pk):
        try:
            objetivo = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({"detail": "Usuario no encontrado"}, status=404)

        objetivo.estado = "ACTIVO"
        objetivo.save()
        return Response(UsuarioSerializer(objetivo).data)


def _usuario_por_correo(request):
    serializer = CorreoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Usuario.objects.filter(correo__iexact=serializer.validated_data["correo"]).first()


class ActivarCuentaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            usuario = consumir_token(serializer.validated_data["token"], "ACTIVACION")
            # Solo una cuenta PENDIENTE se activa; una bloqueada nunca se activa con el enlace.
            if usuario and Usuario.objects.filter(pk=usuario.pk, estado="PENDIENTE").update(
                    estado="ACTIVO", actualizado_en=timezone.now()):
                return Response({"detail": "Cuenta activada."})
            transaction.set_rollback(True)
        return Response(ENLACE_INVALIDO, status=status.HTTP_400_BAD_REQUEST)


class ReenviarActivacionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "reenvio_activacion"

    def post(self, request):
        usuario = _usuario_por_correo(request)
        if usuario and usuario.estado == "PENDIENTE":
            enviar_enlace(usuario, "ACTIVACION")
        return Response(RESPUESTA_GENERICA)


class SolicitarRecuperacionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "recuperacion"

    def post(self, request):
        usuario = _usuario_por_correo(request)
        if usuario and usuario.estado == "ACTIVO":
            enviar_enlace(usuario, "RECUPERACION")
        return Response(RESPUESTA_GENERICA)


class RestablecerPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RestablecerPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            usuario = consumir_token(serializer.validated_data["token"], "RECUPERACION")
            if usuario is None or usuario.estado != "ACTIVO":
                transaction.set_rollback(True)
                return Response(ENLACE_INVALIDO, status=status.HTTP_400_BAD_REQUEST)
            # Si la contraseña no pasa los validadores se lanza ValidationError: la
            # transacción se revierte y el enlace sigue sirviendo para reintentar.
            validar_password(serializer.validated_data["password"], usuario)
            usuario.set_password(serializer.validated_data["password"])
            usuario.save(update_fields=["password", "actualizado_en"])
            TokenCuenta.objects.filter(usuario=usuario, proposito="RECUPERACION", usado_en__isnull=True).delete()
            revocar_sesiones(usuario)
        return Response({"detail": "Contraseña actualizada."})
