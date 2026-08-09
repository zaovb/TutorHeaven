from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.models.session_model import Session
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class SessionDialog(FitDialog):
    """Dialog to create a session.

    Formulario para registrar una sesión de clase: fecha, hora de
    inicio/fin, tema, estado y notas. Al aceptar valida que la hora
    de fin sea posterior a la de inicio y expone el resultado en
    self.session_data (un dict listo para construir una Session).

    Acepta un estudiante opcional para calcular automáticamente si la
    nueva clase está pagada según el modo de pago del paquete vigente,
    y una sesión opcional para editar una existente (precargando los
    campos y conservando su estado de pago).
    """

    def __init__(
        self,
        student: Student | None = None,
        session: Session | None = None,
        date_str: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> None:
        super().__init__()

        self.student = student
        self.session = session

        self.session_data = None

        self.setWindowTitle(
            tr("Edit Session") if session is not None else tr("Add Session")
        )
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)

        if session is not None:
            self.date.setDate(
                QDate.fromString(
                    session.date,
                    "yyyy-MM-dd",
                )
            )
            self.start_time = QTimeEdit(
                QTime.fromString(
                    session.start_time,
                    "HH:mm",
                )
            )
            self.end_time = QTimeEdit(
                QTime.fromString(
                    session.end_time,
                    "HH:mm",
                )
            )
        else:
            self.date.setDate(QDate.currentDate())
            self.start_time = QTimeEdit(
                QTime.currentTime()
            )

            # Por defecto la sesión dura una hora.
            self.end_time = QTimeEdit(
                QTime.currentTime().addSecs(3600)
            )

        # Valores iniciales opcionales (usados desde el calendario).
        if date_str is not None:
            parsed = QDate.fromString(
                date_str,
                "yyyy-MM-dd",
            )

            if parsed.isValid():
                self.date.setDate(parsed)

        if start_time is not None:
            self.start_time.setTime(
                QTime.fromString(
                    start_time,
                    "HH:mm",
                )
            )

        if end_time is not None:
            self.end_time.setTime(
                QTime.fromString(
                    end_time,
                    "HH:mm",
                )
            )

        self.start_time.setDisplayFormat("HH:mm")
        self.end_time.setDisplayFormat("HH:mm")

        self.topic = QLineEdit()

        if session is not None:
            self.topic.setText(session.topic)

        self.status = QComboBox()
        self.status.addItem(
            tr("Pending"),
            "Pending",
        )
        self.status.addItem(
            tr("Completed"),
            "Completed",
        )
        self.status.addItem(
            tr("Cancelled"),
            "Cancelled",
        )

        if session is not None:
            index = self.status.findData(session.status)

            if index >= 0:
                self.status.setCurrentIndex(index)

        self.notes = QLineEdit()

        if session is not None:
            self.notes.setText(session.notes)

        # Estado de pago: se calcula automáticamente. Las clases nuevas
        # nacen pagadas solo si el paquete está "Pay in advance" y pagado;
        # en el resto de casos nacen "Pay later" (sin pagar).
        if session is not None:
            paid = (
                student.session_is_paid(session)
                if student is not None
                else session.paid
            )
        elif student is not None:
            paid = student.session_paid_default()
        else:
            paid = False

        self.paid_label = QLabel(
            tr("✓ Paid")
            if paid
            else tr("Pay later (not paid)")
        )

        if paid:
            self.paid_label.setStyleSheet(
                "color: #2E7D32; font-weight: bold;"
            )
        else:
            self.paid_label.setStyleSheet(
                "color: #E65100; font-weight: bold;"
            )

        form.addRow(tr("Date"), self.date)
        form.addRow(tr("Start Time"), self.start_time)
        form.addRow(tr("End Time"), self.end_time)
        form.addRow(tr("Topic"), self.topic)
        form.addRow(tr("Status"), self.status)
        form.addRow(tr("Notes"), self.notes)
        form.addRow(tr("Payment"), self.paid_label)

        layout.addLayout(form)

        # Progreso: solo al editar una sesión existente. Cada clase
        # registra el avance del alumno en ese día.
        if session is not None:
            progress = QGroupBox(tr("Progress"))
            progress_form = QFormLayout(progress)

            self.conversation_topic = QLineEdit()
            self.conversation_topic.setText(session.conversation_topic)
            self.grammar_learned = QPlainTextEdit()
            self.grammar_learned.setPlainText(
                session.grammar_learned
            )
            self.homework = QPlainTextEdit()
            self.homework.setPlainText(session.homework)
            self.next_topics = QPlainTextEdit()
            self.next_topics.setPlainText(session.next_topics)

            self.homework_done = QCheckBox(
                tr("Completed the homework")
            )
            self.homework_done.setChecked(session.homework_done)

            progress_form.addRow(
                tr("Conversation Topic"),
                self.conversation_topic,
            )
            progress_form.addRow(
                tr("Grammar Learned"),
                self.grammar_learned,
            )
            progress_form.addRow(
                tr("Homework"),
                self.homework,
            )
            progress_form.addRow(
                tr("Next Topics"),
                self.next_topics,
            )
            progress_form.addRow(tr("Homework Done"), self.homework_done)

            layout.addWidget(progress)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_session)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # Enter = siguiente campo (sin cerrar el diálogo).
        enable_enter_to_next(self)

    def accept_session(self) -> None:
        """Valida y recoge los datos de la sesión antes de aceptar."""
        start = self.start_time.time()
        end = self.end_time.time()

        # Una sesión no puede terminar antes de empezar.
        if end <= start:
            QMessageBox.warning(
                self,
                tr("Invalid Session"),
                tr("End time must be after start time."),
            )

            return

        # Al editar se conserva el pago actual; al crear se calcula
        # automáticamente según el paquete del estudiante.
        if self.session is not None:
            paid = (
                self.student.session_is_paid(self.session)
                if self.student is not None
                else self.session.paid
            )
        elif self.student is not None:
            paid = self.student.session_paid_default()
        else:
            paid = False

        # No se permiten dos clases del mismo alumno a la misma hora.
        if self.student is not None:
            proposed = Session(
                date=self.date.date().toString("yyyy-MM-dd"),
                start_time=start.toString("HH:mm"),
                end_time=end.toString("HH:mm"),
                topic=self.topic.text(),
                status=self.status.currentData(),
                notes=self.notes.text(),
                paid=paid,
            )

            if self.student.overlaps_other_sessions(proposed):
                QMessageBox.warning(
                    self,
                    tr("Overlapping Classes"),
                    tr(
                        "This class overlaps another class of {0}. "
                        "Choose a different time."
                    ).format(self.student.name),
                )

                return

        self.session_data = {
            "date": self.date.date().toString(
                "yyyy-MM-dd"
            ),
            "start_time": start.toString(
                "HH:mm"
            ),
            "end_time": end.toString(
                "HH:mm"
            ),
            "topic": self.topic.text(),
            "status": self.status.currentData(),
            "notes": self.notes.text(),
            "paid": paid,
            "conversation_topic": (
                self.conversation_topic.text()
                if self.session is not None
                else ""
            ),
            "grammar_learned": (
                self.grammar_learned.toPlainText()
                if self.session is not None
                else ""
            ),
            "homework": (
                self.homework.toPlainText()
                if self.session is not None
                else ""
            ),
            "next_topics": (
                self.next_topics.toPlainText()
                if self.session is not None
                else ""
            ),
            "homework_done": (
                self.homework_done.isChecked()
                if self.session is not None
                else False
            ),
        }

        self.accept()
