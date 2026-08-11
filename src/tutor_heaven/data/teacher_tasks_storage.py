import json
from pathlib import Path

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.models.teacher_task import TeacherTask


# Ruta absoluta al archivo de tareas del profesor. Se resuelve desde
# este archivo (data/teacher_tasks_storage.py -> raíz del proyecto)
# igual que el resto de datos de la aplicación.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

TEACHER_TASKS_FILE = PROJECT_ROOT / "data" / "teacher_tasks.json"

# Tareas eliminadas (papelera): se guardan en un archivo aparte para no
# tocar la lista activa. Allí viven hasta que se restauran o se eliminan
# permanentemente.
DELETED_TASKS_FILE = PROJECT_ROOT / "data" / "deleted_teacher_tasks.json"


def same_task(a: TeacherTask, b: TeacherTask) -> bool:
    """True si ambas referencias describen la misma tarea."""
    return (
        a.student == b.student
        and a.text == b.text
        and a.created_at == b.created_at
    )


def load_teacher_tasks() -> list[TeacherTask]:
    """Carga todas las tareas del profesor desde data/teacher_tasks.json.

    Si el archivo no existe todavía (primera ejecución) devuelve una
    lista vacía.
    """
    return _load_from(TEACHER_TASKS_FILE)


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


def _load_from(path: Path) -> list[TeacherTask]:
    """Carga la lista de tareas (dicts) desde el archivo dado."""
    if not path.exists():
        return []

    data = json.loads(
        path.read_text(
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


def load_deleted_teacher_tasks() -> list[TeacherTask]:
    """Carga la lista de tareas eliminadas (papelera).

    Estas tareas ya no aparecen en la aplicación principal; solo se ven
    desde el portal de "Tareas eliminadas" para restaurarlas o borrarlas
    definitivamente.
    """
    return _load_from(DELETED_TASKS_FILE)


def save_deleted_teacher_tasks(
    tasks: list[TeacherTask],
) -> None:
    """Persiste la lista de tareas eliminadas del profesor."""
    DELETED_TASKS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    DELETED_TASKS_FILE.write_text(
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

    get_bus().teacherTasksChanged.emit()


def delete_teacher_task(task: TeacherTask) -> None:
    """Mueve una tarea del profesor de la lista activa a la papelera."""
    active = [
        t
        for t in load_teacher_tasks()
        if not same_task(t, task)
    ]

    deleted = [
        t
        for t in load_deleted_teacher_tasks()
        if not same_task(t, task)
    ]

    deleted.append(task)

    save_teacher_tasks(active)
    save_deleted_teacher_tasks(deleted)


def restore_teacher_task(task: TeacherTask) -> None:
    """Devuelve una tarea eliminada de la papelera a la lista activa."""
    deleted = [
        t
        for t in load_deleted_teacher_tasks()
        if not same_task(t, task)
    ]

    active = [
        *load_teacher_tasks(),
        task,
    ]

    save_deleted_teacher_tasks(deleted)
    save_teacher_tasks(active)


def purge_teacher_task(task: TeacherTask) -> None:
    """Elimina para siempre una tarea de la papelera del profesor."""
    deleted = [
        t
        for t in load_deleted_teacher_tasks()
        if not same_task(t, task)
    ]

    save_deleted_teacher_tasks(deleted)