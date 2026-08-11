import json
from datetime import datetime
from pathlib import Path

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.models.package_model import Package
from tutor_heaven.models.payment_model import Payment
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student


# Ruta absoluta al archivo de datos. Se resuelve desde este archivo
# (data/student_storage.py -> raíz del proyecto) para que funcione
# sin importar el directorio de trabajo desde el que se ejecute la app.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = PROJECT_ROOT / "data" / "students.json"


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

    data = []

    # Convierte cada Student (dataclass) en un dict serializable a JSON.
    for student in students:
        data.append(
            {
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
                "sessions": [
                    {
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
                    for session in student.sessions
                ],
            }
        )

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


def load_students() -> list[Student]:
    """Carga la lista de estudiantes desde data/students.json.

    Si el archivo no existe todavía (primera ejecución) devuelve una
    lista vacía. Reconstruye los objetos Student y Session a partir
    de los diccionarios guardados.
    """
    if not DATA_FILE.exists():
        return []

    data = json.loads(
        DATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    students = []

    for item in data:
        # Reconstruye cada sesión guardada dentro del estudiante.
        sessions = [
            Session(
                date=session["date"],
                start_time=session["start_time"],
                end_time=session["end_time"],
                topic=session["topic"],
                status=session["status"],
                notes=session["notes"],
                # get() con default para tolerar archivos viejos
                # que aún no tenían estos campos.
                paid=session.get(
                    "paid",
                    False,
                ),
                grammar_learned=session.get(
                    "grammar_learned",
                    "",
                ),
                homework=session.get(
                    "homework",
                    "",
                ),
                next_topics=session.get(
                    "next_topics",
                    "",
                ),
                conversation_topic=session.get(
                    "conversation_topic",
                    "",
                ),
                homework_done=session.get(
                    "homework_done",
                    False,
                ),
                created_at=session.get(
                    "created_at",
                    "",
                ),
            )
            for session in item.get(
                "sessions",
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

        students.append(student)

    return students
