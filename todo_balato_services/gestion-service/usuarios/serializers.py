from rest_framework import serializers
from .models import Usuario


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "password"]

    def create(self, validated_data):
        # Ignoramos cualquier "rol" que llegue en el body: siempre CLIENTE
        return Usuario.objects.create_user(
            correo=validated_data["correo"],
            password=validated_data["password"],
            nombre=validated_data["nombre"],
            apellido=validated_data["apellido"],
            rol="CLIENTE",
            estado="ACTIVO",
        )


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "rol", "estado", "creado_en"]