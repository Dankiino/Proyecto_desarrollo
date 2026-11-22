from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Usuario


def validar_password(password, usuario=None):
    try:
        validate_password(password, usuario)
    except DjangoValidationError as e:
        raise serializers.ValidationError({"password": list(e.messages)})


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "password"]

    def validate(self, attrs):
        validar_password(attrs["password"], Usuario(
            nombre=attrs["nombre"], apellido=attrs["apellido"], correo=attrs["correo"]))
        return attrs

    def create(self, validated_data):
        # Ignoramos cualquier "rol" que llegue en el body: siempre CLIENTE.
        # La cuenta queda PENDIENTE hasta que se use el enlace de activación.
        return Usuario.objects.create_user(
            correo=validated_data["correo"],
            password=validated_data["password"],
            nombre=validated_data["nombre"],
            apellido=validated_data["apellido"],
            rol="CLIENTE",
            estado="PENDIENTE",
        )


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "rol", "estado", "creado_en"]


class CorreoSerializer(serializers.Serializer):
    correo = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)


class RestablecerPasswordSerializer(TokenSerializer):
    password = serializers.CharField(write_only=True, max_length=128)
