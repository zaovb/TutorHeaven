from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTimeEdit,
    QVBoxLayout,
)

from tutor_heaven.i18n import tr
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.dialog_utils import make_value_field_manual
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class AddSessionDialog(QDialog):
    """Dialog to schedule a class for any student.

    Formulario para agendar una clase para cualquiera de los
    estudiantes: elige el estudiante, fecha, hora de inicio/fin, tema,
    estado y notas. Al aceptar valida la hora y que no solape con otra
    clase del mismo estudiante, y expone el resultado en
    self.created_session y self.created_for_student (listos para
    guardar y consumir la clase si es "Completed").
    """

    def __init__(self, students: list[Student]) -> None:
        super().__init__()

        self.students = students

        self.created_session: Session | None = None
        self.created_for_student: Student | None = None

        self.setWindowTitle(tr("Add Session"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.student_combo = QComboBox()

        for student in self.students:
            self.student_combo.addItem(
                student.name,
                student,
            )

        form.addRow(tr("Student"), self.student_combo)

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        form.addRow(tr("Date"), self.date)

        self.start_time = QTimeEdit()
        self.end_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.end_time.setDisplayFormat("HH:mm")

        self.start_time.setTime(QTime(9, 0))
        self.end_time.setTime(QTime(10, 0))

        form.addRow(tr("Start Time"), self.start_time)
        form.addRow(tr("End Time"), self.end_time)

        self.topic = QLineEdit()
        form.addRow(tr("Topic"), self.topic)

        self.status = QComboBox()
        self.status.addItem(tr("Pending"), "Pending")
        self.status.addItem(tr("Completed"), "Completed")
        self.status.addItem(tr("Cancelled"), "Cancelled")

        form.addRow(tr("Status"), self.status)

        self.notes = QLineEdit()
        form.addRow(tr("Notes"), self.notes)

        self.paid_label = QLabel()
        self.paid_label.setStyleSheet(
            "color: #2E7D32; font-weight: bold;"
        )

        form.addRow(tr("Payment"), self.paid_label)

        self.student_combo.currentIndexChanged.connect(
            self.update_paid_hint
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_session)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        enable_enter_to_next(self)

        # Los valores solo se editan con el teclado: sin scroll ni flechas.
        for field in (
            self.student_combo,
            self.date,
            self.start_time,
            self.end_time,
            self.status,
        ):
            make_value_field_manual(field)

        self.update_paid_hint()

    def selected_student(self) -> Student | None:
        """Devuelve el estudiante elegido en el selector."""
        return self.student_combo.currentData()

    def update_paid_hint(self) -> None:
        """Muestra si la clase nacerá pagada según el paquete FIFO."""
        student = self.selected_student()

        if student is None:
            return

        if student.session_paid_default():
            self.paid_label.setText(tr("✓ Paid"))
            self.paid_label.setStyleSheet(
                "color: #2E7D32; font-weight: bold;"
            )
        else:
            self.paid_label.setText(tr("Pay later (not paid)"))
            self.paid_label.setStyleSheet(
                "color: #E65100; font-weight: bold;"
            )

    def accept_session(self) -> None:
        """Valida y crea la sesión antes de aceptar."""
        start = self.start_time.time()
        end = self.end_time.time()

        if end <= start:
            QMessageBox.warning(
                self,
                tr("Invalid Session"),
                tr("End time must be after start time."),
            )

            return

        student = self.selected_student()

        if student is None:
            return

        session = Session(
            date=self.date.date().toString("yyyy-MM-dd"),
            start_time=start.toString("HH:mm"),
            end_time=end.toString("HH:mm"),
            topic=self.topic.text(),
            status=self.status.currentData(),
            notes=self.notes.text(),
            paid=student.session_paid_default(),
        )

        if student.overlaps_other_sessions(session):
            QMessageBox.warning(
                self,
                tr("Overlapping Classes"),
                tr(
                    "This class overlaps another class of {0}. "
                    "Choose a different time."
                ).format(student.name),
            )

            return

        self.created_session = session
        self.created_for_student = student

        self.accept()
