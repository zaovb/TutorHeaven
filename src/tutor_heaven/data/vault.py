"""Bóveda de Obsidian con una nota por estudiante.

Genera un archivo Markdown por estudiante dentro de una carpeta que
puede abrirse como bóveda en Obsidian (y un índice con enlaces a todos
los estudiantes para navegar el histórico). La bóveda es opcional: se
activa/desactiva desde Configuración y, cuando está activa, se
regenera sola cada vez que cambian los datos (estudiantes, sesiones
o paquetes).

Los cambios en los archivos de la bóveda son solo de ida: el programa
escribe, no lee; cualquier nota que el usuario añada a mano desde
Obsidian se conserva.
"""

import json
from pathlib import Path

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.data.student_storage import load_students
from tutor_heaven.i18n import tr

# Ruta por defecto de la bóveda (data/vault del proyecto).
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_VAULT = PROJECT_ROOT / "data" / "vault"

# Nombre del índice con enlaces a todos los estudiantes.
INDEX_NAME = "_Estudiantes.md"

# Manifest interno con los archivos generados por nosotros. Sirve para
# borrar solo los que creamos (p. ej. al eliminar un estudiante) sin
# tocar notas que el usuario añada a mano.
MANIFEST_NAME = "_tutor_heaven.json"


def vault_dir() -> Path:
    """Carpeta de la bóveda (la configurada o la ruta por defecto)."""
    settings = get_settings()

    if settings.vault_path.strip():
        return Path(settings.vault_path).expanduser()

    return DEFAULT_VAULT


def safe_name(name: str) -> str:
    """Nombre de archivo seguro a partir del nombre de un estudiante."""
    for char in '/\\:*?"<>|':
        name = name.replace(char, "-")

    return name.strip() or "estudiante"


def _money(value: float) -> str:
    return f"$ {value:.2f}"


def _classes_left_text(student) -> str:
    """Clases restantes: disponibles o por pagar."""
    if student.classes_left >= 0:
        return (
            f"{student.classes_left} "
            f"{tr('classes available')}"
        )

    return (
        f"{-student.classes_left} "
        f"{tr('classes owed')}"
    )


def student_markdown(student) -> str:
    """Contenido Markdown de la nota de un estudiante."""
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
            f"{tr('Active') if student.is_active else tr('Former')}"
        ),
        (
            f"- **{tr('Classes Purchased')}:** "
            f"{student.classes_purchased}"
        ),
        (
            f"- **{tr('Classes Taken')}:** "
            f"{student.classes_taken}"
        ),
        f"- **{tr('Classes Left')}:** {_classes_left_text(student)}",
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
                f"- **{tr('Classes Purchased')}:** "
                f"{package.classes_purchased}"
            )
            lines.append(
                f"- **{tr('Classes Taken')}:** "
                f"{package.classes_taken}"
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
                f"### {session.date} {session.start_time} — "
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


def index_markdown(names: list[str]) -> str:
    """Índice con enlaces wiki de Obsidian a cada estudiante."""
    lines = [
        f"# {tr('Students')}",
        "",
    ]

    for name in sorted(names):
        lines.append(f"- [[{name}]]")

    return "\n".join(lines) + "\n"


def _write_vault() -> None:
    """Escribe (o actualiza) la nota de cada estudiante en la bóveda."""
    directory = vault_dir()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    students = load_students()

    generated = []

    for student in students:
        fname = f"{safe_name(student.name)}.md"
        generated.append(fname)

        (directory / fname).write_text(
            student_markdown(student),
            encoding="utf-8",
        )

    (directory / INDEX_NAME).write_text(
        index_markdown(
            [student.name for student in students]
        ),
        encoding="utf-8",
    )

    # Limpieza segura: borra solo las notas generadas por nosotros
    # correspondientes a estudiantes que ya no existen.
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

    for fname in old.get("generated", []):
        if fname in generated:
            continue

        target = directory / fname

        if target.exists():
            try:
                target.unlink()
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