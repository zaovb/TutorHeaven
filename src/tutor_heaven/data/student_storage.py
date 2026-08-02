import json
from pathlib import Path

from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student


DATA_FILE = Path("data/students.json")


def save_students(
    students: list[Student],
) -> None:
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = []

    for student in students:
        data.append(
            {
                "name": student.name,
                "student_type": student.student_type,
                "email": student.email,
                "phone": student.phone,
                "classes_purchased": student.classes_purchased,
                "classes_taken": student.classes_taken,
                "hourly_price": student.hourly_price,
                "payment_mode": student.payment_mode,
                "payment_status": student.payment_status,
                "notes": student.notes,
                "sessions": [
                    {
                        "date": session.date,
                        "start_time": session.start_time,
                        "end_time": session.end_time,
                        "topic": session.topic,
                        "status": session.status,
                        "notes": session.notes,
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


def load_students() -> list[Student]:
    if not DATA_FILE.exists():
        return []

    data = json.loads(
        DATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    students = []

    for item in data:
        sessions = [
            Session(
                date=session["date"],
                start_time=session["start_time"],
                end_time=session["end_time"],
                topic=session["topic"],
                status=session["status"],
                notes=session["notes"],
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

        students.append(
            Student(
                name=item["name"],
                student_type=item["student_type"],
                email=item["email"],
                phone=item["phone"],
                classes_purchased=item["classes_purchased"],
                classes_taken=item["classes_taken"],
                hourly_price=item["hourly_price"],
                payment_mode=item["payment_mode"],
                payment_status=item["payment_status"],
                notes=item["notes"],
                sessions=sessions,
            )
        )

    return students
