"""Operaciones de Comercio hacia Catálogo. Pendiente de DEA-46: hoy fallan de forma segura."""

from dataclasses import dataclass
from uuid import UUID


class InventarioNoDisponible(Exception):
    pass


@dataclass(frozen=True)
class LineaReserva:
    producto_id: str
    cantidad: int


@dataclass(frozen=True)
class OrdenReserva:
    id: UUID
    cliente_id: UUID
    lineas: tuple[LineaReserva, ...]


def reservar(orden):
    """Reserva todas las líneas de una orden o de un checkout aún no persistido."""
    raise InventarioNoDisponible("Pendiente DEA-46")


def consolidar(orden):
    """Baja stock físico y reservado (idempotente por orden)."""
    raise InventarioNoDisponible("Pendiente DEA-46")


def liberar(orden):
    """Baja solo el stock reservado (idempotente por orden)."""
    raise InventarioNoDisponible("Pendiente DEA-46")
