"""Bóveda de Obsidian con una carpeta por estudiante.

Cada estudiante tiene su propia carpeta dentro de "Estudiantes" o
"Eliminados" con dos archivos generados por el programa:

- ``Historial.md``: información general, sesiones y paquetes.
- ``Tareas.md``: tareas extraídas de las sesiones.

Además se generan versiones PDF de cada archivo para facilitar
la compartición.

El usuario puede añadir cualquier otro archivo dentro de la carpeta
del estudiante (notas, recursos, etc.) y se conservará.

La bóveda es opcional: se activa/desactiva desde Configuración y,
cuando está activa, se regenera sola cada vez que cambian los datos.
"""

import json
import shutil
from pathlib import Path

from tutor_heaven.data.paths import data_dir
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.data.student_storage import (
    load_deleted_students,
    load_students,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.formatting import format_hours

# Ruta por defecto de la bóveda.  Usa data_dir() para que funcione
# tanto en desarrollo como instalado en /opt/.
DEFAULT_VAULT = data_dir() / "vault"

# Subcarpetas de la bóveda: estudiantes activos y eliminados.
ACTIVE_FOLDER = "Estudiantes"
DELETED_FOLDER = "Eliminados"

# Nombres de los archivos generados por el programa dentro de cada
# carpeta de estudiante.
HISTORIAL_NAME = "Historial.md"
TAREAS_NAME = "Tareas.md"

# Nombres de los PDFs generados.
HISTORIAL_PDF = "Historial.pdf"
TAREAS_PDF = "Tareas.pdf"

# Nombre del índice con enlaces a todos los estudiantes.
INDEX_NAME = "_Estudiantes.md"

# Manifest interno con los archivos generados por nosotros. Sirve para
# borrar solo los que creamos sin tocar archivos de usuario.
# Guarda rutas relativas a la raíz de la bóveda (p. ej.
# "Estudiantes/Andrea/Historial.md").
MANIFEST_NAME = "_tutor_heaven.json"


def vault_dir() -> Path:
    """Carpeta de la bóveda (la configurada o la ruta por defecto)."""
    settings = get_settings()

    if settings.vault_path.strip():
        return Path(settings.vault_path).expanduser()

    return DEFAULT_VAULT


def safe_name(name: str) -> str:
    """Nombre seguro de archivo/carpeta a partir del nombre."""
    for char in '/\\:*?"<>|':
        name = name.replace(char, "-")

    return name.strip() or "estudiante"


def student_dir(student, deleted: bool = False) -> Path:
    """Carpeta de la bóveda para un estudiante."""
    directory = vault_dir()
    folder = ACTIVE_FOLDER if not deleted else DELETED_FOLDER
    return directory / folder / safe_name(student.name)


def _money(value: float) -> str:
    return f"$ {value:.2f}"


def _classes_left_text(student) -> str:
    """Horas restantes: disponibles o por pagar."""
    if student.hours_left >= 0:
        return (
            f"{format_hours(student.hours_left)} "
            f"{tr('hours available')}"
        )

    return (
        f"{format_hours(-student.hours_left)} "
        f"{tr('hours owed')}"
    )


# -- Funciones de generación Markdown ----------------------------------


def student_historial_md(
    student, deleted: bool = False,
) -> str:
    """Archivo ``Historial.md``: info general, sesiones y paquetes.

    Con ``deleted=True`` el estado aparece como "Eliminado" en lugar
    de "Activo"/"Antiguo".
    """
    lines = [
        f"# {student.name}",
        "",
        f"## {tr('General Information')}",
        "",
        f"- **{tr('Enrolled On')}:** {student.enrolled_at}",
        f"- **{tr('Level')}:** {student.level or '—'}",
        f"- **{tr('Email')}:** {student.email or '—'}",
        f"- **{tr('Phone')}:** {student.phone or '—'}",
        (
            f"- **{tr('Status')}:** "
            f"{tr('Eliminated') if deleted else (tr('Active') if student.is_active else tr('Former'))}"
        ),
        (
            f"- **{tr('Hours Purchased')}:** "
            f"{format_hours(student.hours_purchased)}"
        ),
        (
            f"- **{tr('Hours Taken')}:** "
            f"{format_hours(student.hours_taken)}"
        ),
        f"- **{tr('Hours Left')}:** {_classes_left_text(student)}",
        "",
    ]

    if student.notes or student.bio:
        lines.append(f"## {tr('Notes')}")
        lines.append("")

        if student.notes:
            lines.append(student.notes)
            lines.append("")

        if student.bio:
            lines.append(student.bio)
            lines.append("")

    if student.interests:
        lines.append(f"## {tr('Interests')}")
        lines.append("")

        for interest in student.interests:
            lines.append(f"- {interest}")

        lines.append("")

    if student.topics:
        lines.append(f"## {tr('Grammar Topics')}")
        lines.append("")

        for topic in student.topics:
            lines.append(f"- {topic}")

        lines.append("")

    if student.packages:
        lines.append(f"## {tr('Packages')}")
        lines.append("")

        for index, package in enumerate(
            reversed(student.packages),
            start=1,
        ):
            lines.append(
                f"### {tr('Package {0}').format(index)}"
            )
            lines.append("")

            purchased = (
                package.date_of_payment
                or package.date_of_start
                or "—"
            )

            lines.append(
                f"- **{tr('Purchased On')}:** {purchased}"
            )
            lines.append(
                f"- **{tr('Hours Purchased')}:** "
                f"{format_hours(package.hours_purchased)}"
            )
            lines.append(
                f"- **{tr('Hours Taken')}:** "
                f"{format_hours(package.hours_taken)}"
            )
            lines.append(
                f"- **{tr('Hourly Price')}:** "
                f"{_money(package.hourly_price)}"
            )
            lines.append(
                f"- **{tr('Discount')}:** "
                f"{package.discount_percent}%"
            )
            lines.append(
                f"- **{tr('Payment Mode')}:** "
                f"{tr(package.payment_mode)}"
            )
            lines.append(
                f"- **{tr('Payment Status')}:** "
                f"{tr(package.payment_status)}"
            )
            lines.append("")

    if student.sessions:
        lines.append(f"## {tr('Sessions')}")
        lines.append("")

        ordered = sorted(
            student.sessions,
            key=lambda session: session.start_datetime,
            reverse=True,
        )

        for session in ordered:
            lines.append(
                f"### {session.date} "
                f"{session.start_time}–{session.end_time} — "
                f"{tr(session.status)}"
            )
            lines.append("")

            if session.conversation_topic:
                lines.append(
                    f"- **{tr('Conversation Topic')}:** "
                    f"{session.conversation_topic}"
                )

            if session.grammar_learned:
                lines.append(
                    f"- **{tr('Grammar Learned')}:** "
                    f"{session.grammar_learned}"
                )

            if session.homework:
                lines.append(
                    f"- **{tr('Homework')}:** {session.homework}"
                )
                lines.append(
                    f"- **{tr('Homework Done')}:** "
                    f"{tr('Yes') if session.homework_done else tr('No')}"
                )

            if session.next_topics:
                lines.append(
                    f"- **{tr('To Learn Next')}:** "
                    f"{session.next_topics}"
                )

            if session.notes:
                lines.append(
                    f"- **{tr('Notes')}:** {session.notes}"
                )

            lines.append("")

    return "\n".join(lines).strip() + "\n"


def student_tareas_md(
    student, deleted: bool = False,
) -> str:
    """Archivo ``Tareas.md``: tareas extraídas de las sesiones.

    Cada tarea aparece con la fecha de la sesión y su estado.
    """
    lines = [
        f"# {tr('Homework Tasks')} — {student.name}",
        "",
    ]

    if not student.sessions:
        lines.append(f"*{tr('No tasks recorded')}*")
        return "\n".join(lines) + "\n"

    ordered = sorted(
        student.sessions,
        key=lambda session: session.start_datetime,
        reverse=True,
    )

    has_any = False

    for session in ordered:
        if not session.homework:
            continue

        has_any = True

        lines.append(
            f"### {session.date} "
            f"{session.start_time}–{session.end_time}"
        )
        lines.append("")

        lines.append(
            f"- **{tr('Homework')}:** {session.homework}"
        )
        lines.append(
            f"- **{tr('Homework Done')}:** "
            f"{tr('Yes') if session.homework_done else tr('No')}"
        )

        if session.next_topics:
            lines.append(
                f"- **{tr('To Learn Next')}:** "
                f"{session.next_topics}"
            )

        lines.append("")

    if not has_any:
        lines.append(f"*{tr('No tasks recorded')}*")

    return "\n".join(lines).strip() + "\n"


# -- Funciones de generación PDF ----------------------------------------


def student_historial_pdf(
    student, deleted: bool = False,
) -> Path:
    """Genera ``Historial.pdf`` y devuelve la ruta."""
    from tutor_heaven.data.pdf_renderer import render_markdown_to_pdf

    content = student_historial_md(student, deleted=deleted)
    path = student_dir(student, deleted=deleted) / HISTORIAL_PDF
    render_markdown_to_pdf(content, path)
    return path


def student_tareas_pdf(
    student, deleted: bool = False,
) -> Path:
    """Genera ``Tareas.pdf`` y devuelve la ruta."""
    from tutor_heaven.data.pdf_renderer import render_markdown_to_pdf

    content = student_tareas_md(student, deleted=deleted)
    path = student_dir(student, deleted=deleted) / TAREAS_PDF
    render_markdown_to_pdf(content, path)
    return path


def index_markdown(
    active_names: list[str],
    deleted_names: list[str],
) -> str:
    """Índice con enlaces wiki de Obsidian a cada estudiante.

    Los enlaces apuntan al ``Historial.md`` dentro de la carpeta del
    estudiante para que Obsidian abra directamente la nota principal.
    """
    lines = [
        f"# {tr('Students')}",
        "",
        f"## {tr('Active Students')}",
        "",
    ]

    for name in sorted(active_names):
        sname = safe_name(name)
        lines.append(
            f"- [[{ACTIVE_FOLDER}/{sname}/{HISTORIAL_NAME.replace('.md', '')}|{name}]]"
        )

    lines.extend(
        [
            "",
            f"## {tr('Eliminated Students')}",
            "",
        ]
    )

    if not deleted_names:
        lines.append(f"*{tr('No eliminated students')}*")
    else:
        for name in sorted(deleted_names):
            sname = safe_name(name)
            lines.append(
                f"- [[{DELETED_FOLDER}/{sname}/{HISTORIAL_NAME.replace('.md', '')}|{name}]]"
            )

    return "\n".join(lines) + "\n"


def _write_vault() -> None:
    """Escribe (o actualiza) la bóveda de Obsidian.

    Cada estudiante tiene su propia carpeta con ``Historial.md`` y
    ``Tareas.md``.  Los archivos de usuario que el usuario haya
    creado dentro de la carpeta se conservan.
    """
    directory = vault_dir()

    active_dir = directory / ACTIVE_FOLDER
    deleted_dir = directory / DELETED_FOLDER

    active_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    deleted_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    active = load_students()
    deleted = load_deleted_students()

    generated = []

    for student in active:
        folder = safe_name(student.name)
        student_dir_path = active_dir / folder
        student_dir_path.mkdir(exist_ok=True)

        hist_rel = f"{ACTIVE_FOLDER}/{folder}/{HISTORIAL_NAME}"
        tareas_rel = f"{ACTIVE_FOLDER}/{folder}/{TAREAS_NAME}"
        hist_pdf_rel = f"{ACTIVE_FOLDER}/{folder}/{HISTORIAL_PDF}"
        tareas_pdf_rel = f"{ACTIVE_FOLDER}/{folder}/{TAREAS_PDF}"

        generated.append(hist_rel)
        generated.append(tareas_rel)
        generated.append(hist_pdf_rel)
        generated.append(tareas_pdf_rel)

        (student_dir_path / HISTORIAL_NAME).write_text(
            student_historial_md(student),
            encoding="utf-8",
        )

        (student_dir_path / TAREAS_NAME).write_text(
            student_tareas_md(student),
            encoding="utf-8",
        )

        try:
            student_historial_pdf(student)
            student_tareas_pdf(student)
        except Exception:
            import traceback
            traceback.print_exc()

    for student in deleted:
        folder = safe_name(student.name)
        student_dir_path = deleted_dir / folder
        student_dir_path.mkdir(exist_ok=True)

        hist_rel = f"{DELETED_FOLDER}/{folder}/{HISTORIAL_NAME}"
        tareas_rel = f"{DELETED_FOLDER}/{folder}/{TAREAS_NAME}"
        hist_pdf_rel = f"{DELETED_FOLDER}/{folder}/{HISTORIAL_PDF}"
        tareas_pdf_rel = f"{DELETED_FOLDER}/{folder}/{TAREAS_PDF}"

        generated.append(hist_rel)
        generated.append(tareas_rel)
        generated.append(hist_pdf_rel)
        generated.append(tareas_pdf_rel)

        (student_dir_path / HISTORIAL_NAME).write_text(
            student_historial_md(student, deleted=True),
            encoding="utf-8",
        )

        (student_dir_path / TAREAS_NAME).write_text(
            student_tareas_md(student, deleted=True),
            encoding="utf-8",
        )

        try:
            student_historial_pdf(student, deleted=True)
            student_tareas_pdf(student, deleted=True)
        except Exception:
            import traceback
            traceback.print_exc()

    (directory / INDEX_NAME).write_text(
        index_markdown(
            [student.name for student in active],
            [student.name for student in deleted],
        ),
        encoding="utf-8",
    )

    # Limpieza segura: borra solo los archivos generados por nosotros
    # que ya no están en la lista actual (estudiantes eliminados
    # definitivamente).  No toca archivos de usuario ni carpetas.
    manifest_path = directory / MANIFEST_NAME

    try:
        old = (
            json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )
            if manifest_path.exists()
            else {"generated": []}
        )
    except Exception:
        old = {"generated": []}

    for rel in old.get("generated", []):
        if rel in generated:
            continue

        target = directory / rel

        if target.exists():
            try:
                target.unlink()
            except OSError:
                pass

    # Limpiar carpetas de estudiantes que ya no están en el manifest.
    # Si un estudiante pasó a la papelera, su carpeta en Estudiantes/
    # se borra (ya existe la nueva en Eliminados/).  Si se borró
    # definitivamente, su carpeta en Eliminados/ se borra también.
    generated_folders = {
        Path(rel).parent for rel in generated
    }

    for folder in (ACTIVE_FOLDER, DELETED_FOLDER):
        base = directory / folder

        if not base.is_dir():
            continue

        for student_dir in list(base.iterdir()):
            if not student_dir.is_dir():
                continue

            # Ruta relativa de la carpeta del estudiante.
            rel_folder = Path(folder) / student_dir.name

            if rel_folder in generated_folders:
                continue

            try:
                shutil.rmtree(student_dir)
            except OSError:
                pass

    manifest_path.write_text(
        json.dumps(
            {
                "generated": generated,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def clean_generated_files() -> None:
    """Borra todo lo generado por la aplicación (factory reset).

    Elimina las carpetas de estudiantes (con todo lo que contengan),
    el índice y el manifest.  Conserva la estructura de la bóveda
    (.obsidian) y la raíz de Estudiantes/Eliminados/.
    """
    directory = vault_dir()

    for folder in (ACTIVE_FOLDER, DELETED_FOLDER):
        base = directory / folder

        if not base.is_dir():
            continue

        for child in base.iterdir():
            if child.is_dir():
                try:
                    shutil.rmtree(child)
                except OSError:
                    pass
            elif child.is_file():
                try:
                    child.unlink()
                except OSError:
                    pass

    for name in (INDEX_NAME, MANIFEST_NAME):
        target = directory / name

        if target.is_file():
            try:
                target.unlink()
            except OSError:
                pass


def sync_vault() -> None:
    """Regenera la bóveda si está activa (no rompe si falla)."""
    if not get_settings().vault_enabled:
        return

    try:
        _write_vault()
    except Exception:
        import traceback

        traceback.print_exc()


def start_vault_sync() -> None:
    """Conecta la bóveda a los cambios de datos y la genera.

    Se llama una sola vez al arrancar la aplicación. A partir de ahí,
    cualquier cambio en estudiantes, sesiones, paquetes o tareas
    regenera las notas automáticamente.
    """
    from tutor_heaven.data.data_bus import get_bus

    get_bus().studentsChanged.connect(
        sync_vault
    )

    get_bus().teacherTasksChanged.connect(
        sync_vault
    )

    sync_vault()
