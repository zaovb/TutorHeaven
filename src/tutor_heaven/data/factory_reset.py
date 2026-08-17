"""Restablece la aplicación a su estado de fábrica.

Borra todos los datos del programa (estudiantes, tareas, papelera,
configuración y notas generadas de la bóveda) para que la aplicación
vuelva a verse como recién instalada.
"""

from tutor_heaven.data.settings_storage import (
    SETTINGS_FILE,
    reload_settings,
)
from tutor_heaven.data.student_storage import (
    save_deleted_students,
    save_students,
)
from tutor_heaven.data.teacher_tasks_storage import (
    save_deleted_teacher_tasks,
    save_teacher_tasks,
)
from tutor_heaven.data.vault import clean_generated_files


def factory_reset() -> None:
    """Restaura todos los datos al estado de fábrica.

    Vuelve a escribir vacíos los archivos de estudiantes, tareas del
    profesor y sus papeleras (esto también regenera la bóveda y el
    backup con el contenido limpio), y borra la configuración para que
    la próxima lectura devuelva los valores por defecto.
    """
    save_students([])
    save_deleted_students([])
    save_teacher_tasks([])
    save_deleted_teacher_tasks([])

    # Elimina las notas generadas por el programa (no las del usuario).
    clean_generated_files()

    # Sin settings.json la configuración vuelve a los valores por
    # defecto (idioma, tema, backup y bóveda desactivados).
    if SETTINGS_FILE.exists():
        try:
            SETTINGS_FILE.unlink()
        except OSError:
            pass

    reload_settings()