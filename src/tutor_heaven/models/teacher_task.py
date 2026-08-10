from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class TeacherTask:
    """Tarea del profesor asociada a un estudiante.

    Es una pendiente que el tutor se apunta para ese alumno (preparar
    material, corregir algo, contactar a los padres...). Se muestra en
    la pestaña "Tareas del profesor" del perfil como una lista
    marcable como completada, con una nota editable por tarea.
    """

    text: str

    # True cuando el profesor ya la completó.
    done: bool = False

    # Nota libre del profesor sobre esta tarea.
    notes: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
