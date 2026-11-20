from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import Usuario
from .serializers import RegistroSerializer, UsuarioSerializer
from .permissions import EsAdminActivo


class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]


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