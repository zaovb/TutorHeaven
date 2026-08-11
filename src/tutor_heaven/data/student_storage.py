import json
from datetime import datetime
from pathlib import Path

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.data.teacher_tasks_storage import (
    load_teacher_tasks,
    save_teacher_tasks,
)
from tutor_heaven.models.package_model import Package
from tutor_heaven.models.payment_model import Payment
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student


# Ruta absoluta a los archivos de datos. Se resuelve desde este archivo
# (data/student_storage.py -> raíz del proyecto) para que funcione
# sin importar el directorio de trabajo desde el que se ejecute la app.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = PROJECT_ROOT / "data" / "students.json"

# Estudiantes eliminados (papelera): se guardan en un archivo aparte
# para no tocar la lista activa. Allí viven hasta que se restauran o se
# eliminan permanentemente.
DELETED_FILE = PROJECT_ROOT / "data" / "deleted_students.json"


def student_to_dict(student: Student) -> dict:
    """Serializa un Student (dataclass) a un dict plano para JSON."""
    return {
        "name": student.name,
        "student_type": student.student_type,
        "email": student.email,
        "phone": student.phone,
        "hourly_price": student.hourly_price,
        "payment_mode": student.payment_mode,
        "payment_status": student.payment_status,
        "notes": student.notes,
        "enrolled_at": student.enrolled_at,
        "interests": student.interests,
        "level": student.level,
        "topics": student.topics,
        "bio": student.bio,
        "marked_former": student.marked_former,
        "force_active": student.force_active,
        # Registro de pagos (abonos) recibidos.
        "payments": [
            {
                "amount": payment.amount,
                "date": payment.date,
                "note": payment.note,
                "created_at": payment.created_at,
            }
            for payment in student.payments
        ],
        # Las tareas del profesor viven en un archivo propio
        # (data/teacher_tasks.json), no dentro del estudiante.
        "packages": [
            {
                "classes_purchased": package.classes_purchased,
                "classes_taken": package.classes_taken,
                "hourly_price": package.hourly_price,
                "discount_percent": package.discount_percent,
                "payment_mode": package.payment_mode,
                "payment_status": package.payment_status,
                "date_of_payment": package.date_of_payment,
                "date_of_start": package.date_of_start,
            }
            for package in student.packages
        ],
        # Las sesiones también se serializan, anidadas al estudiante.
        # Las eliminadas (papelera) van en su propia lista.
        "sessions": [
            session_to_dict(session)
            for session in student.sessions
        ],
        "deleted_sessions": [
            session_to_dict(session)
            for session in student.deleted_sessions
        ],
    }


def session_to_dict(session: Session) -> dict:
    """Serializa una Session (dataclass) a un dict plano para JSON."""
    return {
        "date": session.date,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "topic": session.topic,
        "status": session.status,
        "notes": session.notes,
        "paid": session.paid,
        "grammar_learned": session.grammar_learned,
        "homework": session.homework,
        "next_topics": session.next_topics,
        "conversation_topic": session.conversation_topic,
        "homework_done": session.homework_done,
        "created_at": session.created_at,
    }


def _session_from_dict(item: dict) -> Session:
    """Reconstruye una Session a partir del dict guardado."""
    return Session(
        date=item["date"],
        start_time=item["start_time"],
        end_time=item["end_time"],
        topic=item["topic"],
        status=item["status"],
        notes=item["notes"],
        # get() con default para tolerar archivos viejos
        # que aún no tenían estos campos.
        paid=item.get(
            "paid",
            False,
        ),
        grammar_learned=item.get(
            "grammar_learned",
            "",
        ),
        homework=item.get(
            "homework",
            "",
        ),
        next_topics=item.get(
            "next_topics",
            "",
        ),
        conversation_topic=item.get(
            "conversation_topic",
            "",
        ),
        homework_done=item.get(
            "homework_done",
            False,
        ),
        created_at=item.get(
            "created_at",
            "",
        ),
    )


def save_students(
    students: list[Student],
) -> None:
    """Persiste la lista completa de estudiantes en data/students.json.

    Cada estudiante y cada sesión se serializa a un diccionario plano
    (lo que JSON puede representar) antes de escribir el archivo.
    """
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = [
        student_to_dict(student)
        for student in students
    ]

    DATA_FILE.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Avisa a todas las vistas para que recarguen (dashboard,
    # lista de estudiantes y perfiles abiertos).
    get_bus().studentsChanged.emit()


def _load_from(path: Path) -> list[Student]:
    """Carga la lista de estudiantes (dicts) desde el archivo dado."""
    if not path.exists():
        return []

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return [
        _student_from_item(item)
        for item in data
    ]


def _student_from_item(item: dict) -> Student:
    """Reconstruye un Student (y sus hijos) a partir del dict guardado."""
    # Reconstruye cada sesión guardada dentro del estudiante.
    sessions = [
        _session_from_dict(session)
        for session in item.get(
            "sessions",
            [],
        )
    ]

    # Sesiones eliminadas (papelera) del estudiante.
    deleted_sessions = [
        _session_from_dict(session)
        for session in item.get(
            "deleted_sessions",
            [],
        )
    ]

    # Reconstruye el historial de paquetes.
    packages = [
        Package(
            classes_purchased=package["classes_purchased"],
            classes_taken=package.get(
                "classes_taken",
                0,
            ),
            hourly_price=package["hourly_price"],
            discount_percent=package.get(
                "discount_percent",
                0,
            ),
            payment_mode=package.get(
                "payment_mode",
                "Pay in advance",
            ),
            payment_status=package.get(
                "payment_status",
                "Pending",
            ),
            date_of_payment=package.get(
                "date_of_payment",
                "",
            ),
            date_of_start=package.get(
                "date_of_start",
                "",
            ),
        )
        for package in item.get(
            "packages",
            [],
        )
    ]

    student = Student(
        name=item["name"],
        student_type=item["student_type"],
        email=item["email"],
        phone=item["phone"],
        hourly_price=item["hourly_price"],
        payment_mode=item["payment_mode"],
        payment_status=item["payment_status"],
        notes=item["notes"],
        sessions=sessions,
        deleted_sessions=deleted_sessions,
        # Default a la fecha de hoy si el archivo viejo no lo trae.
        enrolled_at=item.get(
            "enrolled_at",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        ),
        interests=item.get(
            "interests",
            [],
        ),
        level=item.get(
            "level",
            "",
        ),
        topics=item.get(
            "topics",
            [],
        ),
        bio=item.get(
            "bio",
            "",
        ),
        marked_former=item.get(
            "marked_former",
            False,
        ),
        force_active=item.get(
            "force_active",
            False,
        ),
        packages=packages,
    )

    # Registro de pagos recibidos (tolera archivos viejos sin ellos).
    student.payments = [
        Payment(
            amount=payment.get(
                "amount",
                0.0,
            ),
            date=payment.get(
                "date",
                "",
            ),
            note=payment.get(
                "note",
                "",
            ),
            created_at=payment.get(
                "created_at",
                "",
            ),
        )
        for payment in item.get(
            "payments",
            [],
        )
    ]

    # Migración desde archivos viejos (sin historial de paquetes):
    # se crea un único paquete sintético con los totales que había.
    # Solo aplica si el archivo tiene el formato antiguo (claves de
    # clases a nivel de estudiante); un estudiante nuevo sin paquetes
    # no debe pasar por aquí.
    if not packages and "classes_purchased" in item:
        student.packages.append(
            Package(
                classes_purchased=item["classes_purchased"],
                classes_taken=item["classes_taken"],
                hourly_price=item["hourly_price"],
                # Se calcula el descuento desde el total migrado
                # (no desde student.auto_discount_percent, que
                # aún es 0 porque packages está vacío).
                discount_percent=item.get(
                    "custom_discount_percent",
                    get_settings().discount_for_classes(
                        item["classes_purchased"]
                    ),
                ),
                payment_mode=item["payment_mode"],
                payment_status=item["payment_status"],
                # Sin fechas conocidas; se dejan vacías.
                date_of_payment="",
                date_of_start=student.enrolled_at[:10],
            )
        )

    return student


def load_students() -> list[Student]:
    """Carga la lista de estudiantes desde data/students.json.

    Si el archivo no existe todavía (primera ejecución) devuelve una
    lista vacía. Reconstruye los objetos Student y Session a partir
    de los diccionarios guardados.
    """
    return _load_from(DATA_FILE)


def load_deleted_students() -> list[Student]:
    """Carga la lista de estudiantes eliminados (papelera).

    Estos estudiantes ya no aparecen en la aplicación principal; solo
    se ven desde el portal de "Eliminados" para restaurarlos o
    borrarlos definitivamente.
    """
    return _load_from(DELETED_FILE)


def save_deleted_students(
    students: list[Student],
) -> None:
    """Persiste la lista de estudiantes eliminados en su archivo."""
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    DELETED_FILE.write_text(
        json.dumps(
            [
                student_to_dict(student)
                for student in students
            ],
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    get_bus().studentsChanged.emit()


def delete_student(
    student: Student,
) -> None:
    """Mueve un estudiante de la lista activa a la papelera."""
    active = [
        s
        for s in load_students()
        if s.name != student.name
    ]

    deleted = [
        s
        for s in load_deleted_students()
        if s.name != student.name
    ]

    deleted.append(student)

    save_students(active)
    save_deleted_students(deleted)


def restore_student(
    student: Student,
) -> None:
    """Devuelve un estudiante de la papelera a la lista activa."""
    deleted = [
        s
        for s in load_deleted_students()
        if s.name != student.name
    ]

    active = [
        *load_students(),
        student,
    ]

    save_deleted_students(deleted)
    save_students(active)


def permanently_delete_student(
    student: Student,
) -> None:
    """Elimina para siempre a un estudiante de la papelera.

    Borra su nota de la bóveda de Obsidian (si la genera el programa),
    sus tareas del profesor y, al dejar de existir en los datos, la
    función de limpieza de la bóveda eliminará el archivo Markdown en
    la próxima sincronización.
    """
    deleted = [
        s
        for s in load_deleted_students()
        if s.name != student.name
    ]

    save_deleted_students(deleted)

    # Quita sus tareas del profesor para que no quede información.
    tasks = [
        task
        for task in load_teacher_tasks()
        if task.student != student.name
    ]

    save_teacher_tasks(tasks)
