from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class TeacherTask:
    """Tarea del profesor.

    Es una pendiente que el tutor se apunta (preparar material, corregir
    algo, contactar a los padres...). Puede ser una tarea general (sin
    estudiante asociado, student == "") o estar asignada a un estudiante.
    Se muestra en la pestaña "Tareas del profesor" del menú principal
    como una lista marcable como completada, con una nota editable.
    """

    text: str

    # True cuando el profesor ya la completó.
    done: bool = False

    # Nota libre del profesor sobre esta tarea.
    notes: str = ""

    # Nombre del estudiante al que está asignada. Vacío = tarea general.
    student: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
