"""Sistema de backup en un solo archivo .zip portable.

El backup consolida TODA la información del programa en un único
archivo de texto comprimido que funciona en cualquier sistema y
entorno:

- ``tutor_heaven_backup.json``: datos consolidados (perfil del
  profesor, configuración, estudiantes activos y papelera, tareas del
  profesor activas y papelera). Es el formato autoritativo: restaurar
  un backup lee este JSON y vuelve a escribir cada archivo de datos.
- ``Estudiantes/*.md`` y ``Eliminados/*.md``: las mismas notas
  Markdown legibles de la bóveda de Obsidian, incluidas en el .zip
  para que quien lo descomprima pueda leer el historial sin abrir la
  aplicación.

El programa accede al .zip directamente con el módulo ``zipfile``
(lee y escribe sin necesidad de descomprimir). El usuario, si quiere,
puede descomprimir el archivo y abrir los contenidos en cualquier
editor.
"""

import json
import zipfile
from datetime import datetime
from pathlib import Path

from tutor_heaven.data.settings_storage import (
    dict_to_settings,
    get_settings,
    reload_settings,
    save_settings,
    settings_to_dict,
)
from tutor_heaven.data.student_storage import (
    load_deleted_students,
    load_students,
    save_deleted_students,
    save_students,
    student_to_dict,
    students_from_dicts,
)
from tutor_heaven.data.teacher_tasks_storage import (
    load_deleted_teacher_tasks,
    load_teacher_tasks,
    save_deleted_teacher_tasks,
    save_teacher_tasks,
    task_to_dict,
    task_from_dict,
)
from tutor_heaven.data.vault import (
    ACTIVE_FOLDER,
    DELETED_FOLDER,
    index_markdown,
    safe_name,
    student_markdown,
)

# Ruta absoluta a los datos del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_BACKUP = PROJECT_ROOT / "data" / "tutor_heaven_backup.zip"

# Nombre del JSON consolidado dentro del .zip.
PAYLOAD_NAME = "tutor_heaven_backup.json"

# Versión del formato de backup. Si cambia la estructura, se puede
# migrar (o rechazar) según esta versión al restaurar.
BACKUP_VERSION = 1


def backup_path() -> Path:
    """Ruta del archivo .zip de backup (la configurada o la por defecto)."""
    settings = get_settings()

    if settings.backup_path.strip():
        return Path(settings.backup_path).expanduser()

    return DEFAULT_BACKUP


def collect_payload() -> dict:
    """Reúne todos los datos de la aplicación en un solo dict.

    Es el corazón del backup: concentra configuración, estudiantes
    (activos y papelera) y tareas del profesor (activas y papelera)
    usando los mismos serializadores que los archivos individuales.
    """
    return {
        "version": BACKUP_VERSION,
        "exported_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "settings": settings_to_dict(get_settings()),
        "students": [
            student_to_dict(student)
            for student in load_students()
        ],
        "deleted_students": [
            student_to_dict(student)
            for student in load_deleted_students()
        ],
        "teacher_tasks": [
            task_to_dict(task)
            for task in load_teacher_tasks()
        ],
        "deleted_teacher_tasks": [
            task_to_dict(task)
            for task in load_deleted_teacher_tasks()
        ],
    }


def _markdown_entries() -> dict[str, str]:
    """Notas Markdown legibles (mismo formato que la bóveda de
    Obsidian) para incluir dentro del .zip.

    Devuelve {ruta dentro del zip: contenido}. Los estudiantes
    activos van en "Estudiantes/" y los eliminados en "Eliminados/",
    más el índice con enlaces a todos.
    """
    active = load_students()
    deleted = load_deleted_students()

    entries: dict[str, str] = {}

    for student in active:
        rel = f"{ACTIVE_FOLDER}/{safe_name(student.name)}.md"
        entries[rel] = student_markdown(student)

    for student in deleted:
        rel = f"{DELETED_FOLDER}/{safe_name(student.name)}.md"
        entries[rel] = student_markdown(student, deleted=True)

    entries["_Estudiantes.md"] = index_markdown(
        [student.name for student in active],
        [student.name for student in deleted],
    )

    return entries


def _write_zip(
    target: Path,
    payload: dict,
    markdown: dict[str, str],
) -> None:
    """Escribe el .zip en un destino temporal y lo mueve al final.

    Escribir primero en un archivo temporal y renombrar evita dejar un
    .zip a medias si el proceso se interrumpe a mitad de escritura.
    """
    target = Path(target)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = target.with_name(
        target.name + ".tmp"
    )

    with zipfile.ZipFile(
        temp,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            PAYLOAD_NAME,
            json.dumps(
                payload,
                indent=4,
                ensure_ascii=False,
            ),
        )

        for rel, content in markdown.items():
            archive.writestr(
                rel,
                content,
            )

    temp.replace(target)


def export_backup(target: Path | None = None) -> Path:
    """Exporta un .zip con todos los datos de la aplicación.

    Devuelve la ruta del archivo escrito. No toca los datos actuales:
    solo produce una copia portable. Acepta str o Path.
    """
    target = Path(target) if target else backup_path()

    _write_zip(
        target,
        collect_payload(),
        _markdown_entries(),
    )

    return target


def update_backup() -> Path | None:
    """Actualiza el .zip de backup configurado si está activo.

    Se llama automáticamente al cambiar los datos (igual que la
    bóveda de Obsidian). No rompe si falla; devuelve la ruta del .zip
    actualizado o None si el backup está desactivado.
    """
    if not get_settings().backup_enabled:
        return None

    target = backup_path()

    try:
        return export_backup(target)
    except Exception:
        import traceback

        traceback.print_exc()

        return None


def restore_backup(
    source: Path,
) -> dict:
    """Restaura todos los datos desde un .zip de backup.

    Lee el JSON consolidado directamente del .zip (sin descomprimir)
    y vuelve a escribir cada archivo de datos de la aplicación:
    settings.json, students.json, deleted_students.json,
    teacher_tasks.json y deleted_teacher_tasks.json.

    Devuelve el payload restaurado para que la interfaz pueda avisar
    de qué se restauró. Lanza excepciones si el archivo no es un
    backup válido.
    """
    with zipfile.ZipFile(Path(source), "r") as archive:
        payload = json.loads(
            archive.read(
                PAYLOAD_NAME
            ).decode("utf-8")
        )

    if payload.get("version") != BACKUP_VERSION:
        raise ValueError(
            f"Unsupported backup version: {payload.get('version')}"
        )

    # Configuración: se reescribe y se recarga la cache global.
    save_settings(
        dict_to_settings(
            payload.get("settings", {})
        )
    )

    reload_settings()

    # Estudiantes y papelera.
    save_students(
        students_from_dicts(
            payload.get("students", [])
        )
    )

    save_deleted_students(
        students_from_dicts(
            payload.get("deleted_students", [])
        )
    )

    # Tareas del profesor y su papelera.
    save_teacher_tasks(
        [
            task_from_dict(item)
            for item in payload.get(
                "teacher_tasks",
                [],
            )
        ]
    )

    save_deleted_teacher_tasks(
        [
            task_from_dict(item)
            for item in payload.get(
                "deleted_teacher_tasks",
                [],
            )
        ]
    )

    return payload


def start_backup_sync() -> None:
    """Conecta el backup a los cambios de datos.

    Se llama una sola vez al arrancar la aplicación. A partir de ahí,
    cualquier cambio en estudiantes, sesiones, paquetes o tareas
    actualiza el .zip automáticamente (si está activado).
    """
    from tutor_heaven.data.data_bus import get_bus

    get_bus().studentsChanged.connect(
        update_backup
    )

    get_bus().teacherTasksChanged.connect(
        update_backup
    )

    update_backup()
