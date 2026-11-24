
from django.db import models


class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    mensaje = models.TextField(max_length=2000)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_recepcion"]
        verbose_name = "Mensaje de contacto"
        verbose_name_plural = "Mensajes de contacto"

    def __str__(self):
        return f"{self.nombre} - {self.correo}"
