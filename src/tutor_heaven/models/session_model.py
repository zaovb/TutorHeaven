from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Session:
    """Represents a student session.

    Modelo de una sesión de clase. Fecha y horas se guardan como
    cadenas de texto ("YYYY-MM-DD" y "HH:mm") para simplificar la
    serialización a JSON. created_at se autogenera al crearla.
    paid indica si esa clase concreta ya fue pagada (usado sobre todo
    en modo de pago "Pay later", donde cada clase se paga aparte).

    Los campos de progreso (grammar_learned, homework, next_topics y
    conversation_topic) registran lo trabajado en la clase, lo que se
    deja de tarea para revisar en la siguiente, lo pendiente para la
    próxima clase y el tema de conversación del día.
    """

    date: str

    start_time: str
    end_time: str

    topic: str
    status: str
    notes: str

    paid: bool = False

    grammar_learned: str = ""
    homework: str = ""
    next_topics: str = ""
    conversation_topic: str = ""

    # Indica si el estudiante completó la tarea de la clase anterior.
    homework_done: bool = False

    created_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    @property
    def start_datetime(self) -> datetime:
        """Inicio de la sesión como datetime completo para comparar."""
        return datetime.strptime(
            f"{self.date} {self.start_time}",
            "%Y-%m-%d %H:%M",
        )

    @property
    def end_datetime(self) -> datetime:
        """Fin de la sesión como datetime completo para comparar."""
        return datetime.strptime(
            f"{self.date} {self.end_time}",
            "%Y-%m-%d %H:%M",
        )