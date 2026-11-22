import uuid
from django.db import models


class Orden(models.Model):
    ESTADO_CHOICES = [
        ("PENDIENTE_PAGO", "PENDIENTE_PAGO"),
        ("CONFIRMACION_PENDIENTE", "CONFIRMACION_PENDIENTE"),
        ("CONFIRMADA", "CONFIRMADA"),
        ("RECHAZADA", "RECHAZADA"),
        ("CANCELADA", "CANCELADA"),
        ("VENCIDA", "VENCIDA"),
        ("REVISION_REQUERIDA", "REVISION_REQUERIDA"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente_id = models.UUIDField(db_index=True)  # referencia al Usuario de Gestión, no FK real
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default="PENDIENTE_PAGO")
    moneda = models.CharField(max_length=3, default="CLP")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    idempotency_key = models.CharField(max_length=100, unique=True)
    reserva_expira_en = models.DateTimeField(null=True, blank=True)
    confirmada_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Orden {self.id} ({self.estado})"


class DetalleOrden(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orden = models.ForeignKey(Orden, related_name="lineas", on_delete=models.CASCADE)
    producto_id = models.CharField(max_length=100)  # id de Mongo, es string
    nombre_producto = models.CharField(max_length=255)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=0)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)


class Carrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente_id = models.UUIDField(unique=True, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)


class LineaCarrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carrito = models.ForeignKey(Carrito, related_name="lineas", on_delete=models.CASCADE)
    producto_id = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()

    class Meta:
        unique_together = ("carrito", "producto_id")


class Pago(models.Model):
    ESTADO_CHOICES = [
        ("PENDIENTE", "PENDIENTE"),
        ("APROBADO", "APROBADO"),
        ("RECHAZADO", "RECHAZADO"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orden = models.OneToOneField(Orden, related_name="pago", on_delete=models.CASCADE)
    proveedor = models.CharField(max_length=50, default="webpay_plus")
    token_ws = models.CharField(max_length=255, null=True, blank=True)
    id_externo = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE")
    monto_verificado = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    moneda_verificada = models.CharField(max_length=3, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ("CONFIRMACION_CLIENTE", "CONFIRMACION_CLIENTE"),
        ("CONFIRMACION_ADMIN", "CONFIRMACION_ADMIN"),
    ]
    ESTADO_CHOICES = [
        ("PENDIENTE", "PENDIENTE"),
        ("ENVIADO", "ENVIADO"),
        ("FALLIDO", "FALLIDO"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orden = models.ForeignKey(Orden, related_name="notificaciones", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    destinatario = models.EmailField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE")
    intentos = models.PositiveIntegerField(default=0)
    ultimo_error = models.TextField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)