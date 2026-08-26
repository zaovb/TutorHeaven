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
        """Fin de la sesión como datetime completo para comparar.

        Si la hora de fin es menor que la de inicio, se asume que la
        sesión cruzó medianoche y se suma un día.
        """
        end = datetime.strptime(
            f"{self.date} {self.end_time}",
            "%Y-%m-%d %H:%M",
        )
        if end <= self.start_datetime:
            from datetime import timedelta
            end += timedelta(days=1)
        return end

    def duration_minutes(self) -> int:
        """Duración de la clase en minutos.

        Se calcula restando las horas "HH:mm" (siempre minutos
        enteros, sin redondeos). Si la hora de fin fuera menor que la
        de inicio (solo posible en datos antiguos generados
        automáticamente al cruzar medianoche) se asume que la clase
        cruzó medianoche y se suma el día completo.
        """
        start = datetime.strptime(
            self.start_time,
            "%H:%M",
        )

        end = datetime.strptime(
            self.end_time,
            "%H:%M",
        )

        minutes = round(
            (end - start).total_seconds() / 60
        )

        if minutes < 0:
            minutes += 24 * 60

        return minutes

    def duration_hours(self) -> float:
        """Duración de la clase en horas (ej. 1.0 o 1.5)."""
        return self.duration_minutes() / 60