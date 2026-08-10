import json
from pathlib import Path

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.models.teacher_task import TeacherTask


# Ruta absoluta al archivo de tareas del profesor. Se resuelve desde
# este archivo (data/teacher_tasks_storage.py -> raíz del proyecto)
# igual que el resto de datos de la aplicación.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

TEACHER_TASKS_FILE = PROJECT_ROOT / "data" / "teacher_tasks.json"


def load_teacher_tasks() -> list[TeacherTask]:
    """Carga todas las tareas del profesor desde data/teacher_tasks.json.

    Si el archivo no existe todavía (primera ejecución) devuelve una
    lista vacía.
    """
    if not TEACHER_TASKS_FILE.exists():
        return []

    data = json.loads(
        TEACHER_TASKS_FILE.read_text(
            encoding="utf-8"
        )
    )

    return [
        TeacherTask(
            text=task.get("text", ""),
            done=task.get("done", False),
            notes=task.get("notes", ""),
            # get() con default para tolerar archivos viejos.
            student=task.get(
                "student",
                "",
            ),
            created_at=task.get(
                "created_at",
                "",
            ),
        )
        for task in data
    ]


def save_teacher_tasks(tasks: list[TeacherTask]) -> None:
    """Persiste la lista completa de tareas del profesor.

    Las tareas generales y las asignadas a cada estudiante viven en el
    mismo archivo; el campo ``student`` indica a quién corresponde (o
    queda vacío para las generales).
    """
    TEACHER_TASKS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEACHER_TASKS_FILE.write_text(
        json.dumps(
            [
                {
                    "text": task.text,
                    "done": task.done,
                    "notes": task.notes,
                    "student": task.student,
                    "created_at": task.created_at,
                }
                for task in tasks
            ],
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Avisa a las vistas de tareas para que recarguen.
    get_bus().teacherTasksChanged.emit()