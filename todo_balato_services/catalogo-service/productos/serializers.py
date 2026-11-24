
from rest_framework import serializers

from .repository import obtener_categoria


class ImagenProductoSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2000)
    alt = serializers.CharField(
        allow_blank=False
    )


class ProductoCrearSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)

    descripcion = serializers.CharField(
        allow_blank=False
    )

    precio = serializers.IntegerField(min_value=1)

    stock_fisico = serializers.IntegerField(min_value=0)

    categoria_id = serializers.CharField(max_length=100)

    imagenes = ImagenProductoSerializer(
        many=True,
        allow_empty=False
    )

    def validate_imagenes(self, valor):
        if not 4 <= len(valor) <= 6:
            raise serializers.ValidationError(
                "El producto debe tener entre 4 y 6 imágenes."
            )
        return valor

    def validate_categoria_id(self, valor):
        categoria = obtener_categoria(
            valor,
            solo_activas=True
        )

        if categoria is None:
            raise serializers.ValidationError(
                "La categoría no existe o está inactiva."
            )

        return valor




class CategoriaSerializer(serializers.Serializer):
    identificador = serializers.RegexField(
        regex=r"^[a-z0-9-]+$",
        min_length=1,
        max_length=100,
        required=False,
    )
    nombre = serializers.CharField(
        min_length=2,
        max_length=60,
        allow_blank=False,
    )
    descripcion = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )
    orden = serializers.IntegerField(min_value=0)
    activa = serializers.BooleanField(required=False)


class AjusteInventarioSerializer(serializers.Serializer):
    stock_fisico = serializers.IntegerField(
        min_value=0,
        max_value=2147483647
    )

    motivo = serializers.CharField(
        min_length=1,
        max_length=500,
        allow_blank=False,
        trim_whitespace=True
    )

    def validate(self, attrs):
        campos_permitidos = {"stock_fisico", "motivo"}

        if set(self.initial_data.keys()) - campos_permitidos:
            raise serializers.ValidationError(
                "Solo se permite enviar el stock físico y el motivo."
            )

        if type(self.initial_data.get("stock_fisico")) is not int:
            raise serializers.ValidationError({
                "stock_fisico": "Debe ser un número entero."
            })

        return attrs