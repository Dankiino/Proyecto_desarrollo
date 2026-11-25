import csv
import io

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import TokenCuenta, Usuario
from .serializers import (
    AdministrarUsuarioSerializer, CorreoSerializer, RegistroSerializer,
    RestablecerPasswordSerializer, TokenSerializer, UsuarioSerializer,
    validar_password,
)
from .permissions import EsAdminActivo
from .servicios import consumir_token, enviar_enlace, revocar_sesiones

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_FILAS = 1000
CSV_COLUMNAS_REQUERIDAS = {"nombre", "apellido", "correo", "password"}

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


class UsuarioListView(generics.ListCreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdminActivo]

    def get_queryset(self):
        return Usuario.objects.order_by("correo")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdministrarUsuarioSerializer
        return UsuarioSerializer


class UsuarioDetailView(generics.RetrieveUpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = AdministrarUsuarioSerializer
    permission_classes = [EsAdminActivo]
    http_method_names = ["get", "patch", "head", "options"]

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        with transaction.atomic():
            administradores = list(
                Usuario.objects.select_for_update()
                .filter(rol="ADMIN", estado="ACTIVO")
                .order_by("id")
            )
            instancia = self.get_object()
            serializer = self.get_serializer(instancia, data=request.data, partial=parcial)
            serializer.is_valid(raise_exception=True)
            nuevo_rol = serializer.validated_data.get("rol", instancia.rol)
            if (
                instancia.rol == "ADMIN"
                and instancia.estado == "ACTIVO"
                and nuevo_rol != "ADMIN"
                and not any(admin.pk != instancia.pk for admin in administradores)
            ):
                return Response(
                    {"detail": "No se puede quitar el rol al último administrador activo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self.perform_update(serializer)
        return Response(UsuarioSerializer(serializer.instance).data)


class ImportarUsuariosCSVView(APIView):
    permission_classes = [EsAdminActivo]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        archivo = request.FILES.get("archivo")
        if archivo is None:
            return Response(
                {"detail": "Adjunta el archivo CSV en el campo 'archivo'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if archivo.size > MAX_CSV_BYTES:
            return Response(
                {"detail": "El archivo supera el límite de 5 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contenido = archivo.read()
        if not contenido.strip():
            return Response(
                {
                    "total": 0,
                    "aceptados": [],
                    "rechazados": [{"fila": 0, "correo": "", "razon": "El archivo está vacío."}],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            texto = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "El archivo debe estar codificado como UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lector = csv.DictReader(io.StringIO(texto, newline=""))
        encabezados = [nombre.strip().lower() for nombre in (lector.fieldnames or [])]
        if (
            not encabezados
            or len(encabezados) != len(set(encabezados))
            or not CSV_COLUMNAS_REQUERIDAS.issubset(encabezados)
            or set(encabezados) - (CSV_COLUMNAS_REQUERIDAS | {"rol"})
        ):
            return Response(
                {
                    "total": 0,
                    "aceptados": [],
                    "rechazados": [{
                        "fila": 1,
                        "correo": "",
                        "razon": "Encabezados inválidos. Requeridos: nombre, apellido, correo, password; rol es opcional.",
                    }],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        aceptados = []
        rechazados = []
        correos_vistos = set()
        total = 0
        for fila, fila_datos in enumerate(lector, start=2):
            total += 1
            correo = (fila_datos.get("correo") or "").strip()
            if None in fila_datos:
                rechazados.append({
                    "fila": fila,
                    "correo": correo,
                    "razon": "La fila contiene más columnas que el encabezado.",
                })
                continue
            if total > MAX_CSV_FILAS:
                rechazados.append({
                    "fila": fila,
                    "correo": correo,
                    "razon": f"Se superó el máximo de {MAX_CSV_FILAS} filas por archivo.",
                })
                continue

            datos = {
                nombre.strip().lower(): (valor or "").strip()
                for nombre, valor in fila_datos.items()
                if nombre is not None
            }
            if not datos.get("rol"):
                datos.pop("rol", None)
            correo_clave = correo.casefold()
            if correo and (
                correo_clave in correos_vistos
                or Usuario.objects.filter(correo__iexact=correo).exists()
            ):
                rechazados.append({
                    "fila": fila,
                    "correo": correo,
                    "razon": "El correo ya está registrado o repetido en el archivo.",
                })
                continue
            if correo:
                correos_vistos.add(correo_clave)

            serializer = AdministrarUsuarioSerializer(data=datos)
            if not serializer.is_valid():
                razones = []
                for campo, errores in serializer.errors.items():
                    mensajes = [str(error) for error in errores]
                    razones.append(f"{campo}: {', '.join(mensajes)}")
                rechazados.append({
                    "fila": fila,
                    "correo": correo,
                    "razon": "; ".join(razones),
                })
                continue

            try:
                with transaction.atomic():
                    usuario = serializer.save()
            except IntegrityError:
                rechazados.append({
                    "fila": fila,
                    "correo": correo,
                    "razon": "El correo ya está registrado.",
                })
                continue

            aceptados.append({
                "fila": fila,
                "correo": usuario.correo,
                "id": str(usuario.pk),
            })

        resultado = {
            "total": total,
            "aceptados": aceptados,
            "rechazados": rechazados,
            "regla": "Procesamiento por fila: las filas válidas se guardan aunque otras sean rechazadas.",
        }
        return Response(resultado, status=status.HTTP_200_OK)


class BloquearUsuarioView(APIView):
    permission_classes = [EsAdminActivo]

    def post(self, request, pk):
        if str(request.user.id) == str(pk):
            return Response({"detail": "No puedes bloquearte a ti mismo"}, status=400)

        with transaction.atomic():
            administradores = list(
                Usuario.objects.select_for_update()
                .filter(rol="ADMIN", estado="ACTIVO")
                .order_by("id")
            )
            try:
                objetivo = Usuario.objects.select_for_update().get(pk=pk)
            except Usuario.DoesNotExist:
                return Response({"detail": "Usuario no encontrado"}, status=404)

            if (
                objetivo.rol == "ADMIN"
                and objetivo.estado == "ACTIVO"
                and not any(admin.pk != objetivo.pk for admin in administradores)
            ):
                return Response({"detail": "No se puede bloquear al último administrador activo"}, status=400)

            objetivo.estado = "BLOQUEADO"
            objetivo.save(update_fields=["estado", "actualizado_en"])
            revocar_sesiones(objetivo)
        return Response(UsuarioSerializer(objetivo).data)


class DesbloquearUsuarioView(APIView):
    permission_classes = [EsAdminActivo]

    def post(self, request, pk):
        with transaction.atomic():
            try:
                objetivo = Usuario.objects.select_for_update().get(pk=pk)
            except Usuario.DoesNotExist:
                return Response({"detail": "Usuario no encontrado"}, status=404)

            objetivo.estado = "ACTIVO"
            objetivo.save(update_fields=["estado", "actualizado_en"])
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
