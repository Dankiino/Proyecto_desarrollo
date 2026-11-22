"""Operaciones de Comercio hacia Catálogo. Pendiente de DEA-46: hoy fallan de forma segura."""


class InventarioNoDisponible(Exception):
    pass


def reservar(orden):
    """Reserva todas las líneas de la orden (idempotente por orden)."""
    raise InventarioNoDisponible("Pendiente DEA-46")


def consolidar(orden):
    """Baja stock físico y reservado (idempotente por orden)."""
    raise InventarioNoDisponible("Pendiente DEA-46")


def liberar(orden):
    """Baja solo el stock reservado (idempotente por orden)."""
    raise InventarioNoDisponible("Pendiente DEA-46")
