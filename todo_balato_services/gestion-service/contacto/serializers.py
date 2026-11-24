
from rest_framework import serializers
from .models import MensajeContacto


class MensajeContactoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(
        min_length=2,
        max_length=100,
        trim_whitespace=True,
        error_messages={
            "blank": "Debes ingresar tu nombre.",
            "min_length": "El nombre debe tener al menos 2 caracteres.",
            "max_length": "El nombre no puede superar los 100 caracteres.",
            "required": "El nombre es obligatorio.",
        },
    )

    correo = serializers.EmailField(
        error_messages={
            "invalid": "Ingresa un correo electrónico válido.",
            "blank": "Debes ingresar tu correo electrónico.",
            "required": "El correo electrónico es obligatorio.",
        },
    )

    mensaje = serializers.CharField(
        min_length=10,
        max_length=2000,
        trim_whitespace=True,
        error_messages={
            "blank": "Debes escribir un mensaje.",
            "min_length": "El mensaje debe tener al menos 10 caracteres.",
            "max_length": "El mensaje no puede superar los 2000 caracteres.",
            "required": "El mensaje es obligatorio.",
        },
    )

    class Meta:
        model = MensajeContacto
        fields = [
            "id",
            "nombre",
            "correo",
            "mensaje",
            "fecha_recepcion",
        ]
        read_only_fields = ["id", "fecha_recepcion"]
