from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Payment:
    """Record of a payment received from the student.

    Registro de un pago (abono) recibido del estudiante. Cada abono
    guarda la cantidad, la fecha y una nota opcional. La suma de estos
    registros es la cantidad efectivamente cobrada (ver
    Student.amount_paid); sirve sobre todo para pagos parciales que no
    se reflejan en el estado binario de los paquetes.
    """

    # Cantidad pagada en este abono (siempre positiva).
    amount: float

    # Fecha del pago (formato "YYYY-MM-DD").
    date: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )

    # Nota opcional (por qué concepto, método de pago, etc.).
    note: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
