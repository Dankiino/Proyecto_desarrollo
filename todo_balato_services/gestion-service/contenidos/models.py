from django.conf import settings
from django.db import models


class Tema(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    nombre = models.CharField(max_length=50)
    color_primario = models.CharField(max_length=7)
    color_secundario = models.CharField(max_length=7)
    color_fondo = models.CharField(max_length=7)
    color_texto = models.CharField(max_length=7)
    color_acento = models.CharField(max_length=7)
    activo = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class ContenidoPagina(models.Model):
    TIPO_CHOICES = [("texto", "texto"), ("imagen", "imagen"), ("enlace", "enlace")]

    pagina = models.CharField(max_length=20)
    clave = models.CharField(max_length=60)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.TextField()
    texto_alternativo = models.CharField(max_length=200, blank=True, default="")
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pagina", "clave"], name="uniq_pagina_clave")
        ]

    def __str__(self):
        return f"{self.pagina}.{self.clave}"
