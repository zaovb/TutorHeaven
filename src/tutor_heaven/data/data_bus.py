"""Bus de señales global para refrescar las vistas.

Cada vez que los datos de estudiantes se guardan en disco
(save_students) se emite studentsChanged. Todas las vistas que
muestran datos de estudiantes se conectan a esta señal para recargar,
de modo que un cambio hecho desde cualquier pestaña (dashboard,
calendario, perfil...) se refleja en todas las demás.
"""

from PySide6.QtCore import QObject, Signal


class DataBus(QObject):
    """Señal central de cambios en los datos de estudiantes."""

    studentsChanged = Signal()


_bus: DataBus | None = None


def get_bus() -> DataBus:
    """Devuelve la instancia única del bus de datos."""
    global _bus

    if _bus is None:
        _bus = DataBus()

    return _bus
