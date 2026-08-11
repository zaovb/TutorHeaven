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
    QScrollArea,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.i18n import tr
from tutor_heaven.models.session_model import Session
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class SessionEditDialog(FitDialog):
    """Dialog to edit an existing session.

    Permite corregir cualquier dato de una sesión ya registrada: fecha,
    horas, tema, estado, notas, estado de pago y el progreso de la
    clase (gramática, tarea, próximos temas y si completó la tarea).

    Al aceptar expone en self.edited_session la sesión actualizada
    (mutada en su lugar) y en self.was_completed si la sesión estaba
    completada antes de la edición, para que el perfil ajuste la clase
    consumida si el estado cambió entre "Completed" y otro.
    """

    def __init__(
        self,
        student,
        session: Session,
    ) -> None:
        super().__init__()

        self.student = student
        self.session = session
        self.edited_session: Session | None = None
        self.was_completed = session.status == "Completed"

        self.setWindowTitle(tr("Edit Session"))
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        body = QWidget()
        body_layout = QVBoxLayout(body)

        # ---------- Información de la clase ----------

        info_group = QGroupBox(tr("Class Information"))
        info_form = QFormLayout()

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.date.setDate(
            QDate.fromString(
                session.date,
                "yyyy-MM-dd",
            )
        )

        info_form.addRow(tr("Date"), self.date)

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(
            QTime.fromString(
                session.start_time,
                "HH:mm",
            )
        )

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setTime(
            QTime.fromString(
                session.end_time,
                "HH:mm",
            )
        )

        info_form.addRow(tr("Start Time"), self.start_time)
        info_form.addRow(tr("End Time"), self.end_time)

        self.topic = QLineEdit(session.topic)
        info_form.addRow(tr("Topic"), self.topic)

        self.status = QComboBox()
        self.status.addItem(tr("Pending"), "Pending")
        self.status.addItem(tr("Completed"), "Completed")
        self.status.addItem(tr("Cancelled"), "Cancelled")

        index = self.status.findData(session.status)

        if index >= 0:
            self.status.setCurrentIndex(index)

        info_form.addRow(tr("Status"), self.status)

        self.paid = QCheckBox(tr("Paid"))

        # En "Pay in advance" el estado de pago se deriva de los
        # paquetes y no se puede forzar a mano.
        self.paid.setEnabled(
            student.payment_mode != "Pay in advance"
        )

        self.paid.setChecked(session.paid)

        info_form.addRow(tr("Payment"), self.paid)

        self.notes = QLineEdit(session.notes)
        info_form.addRow(tr("Notes"), self.notes)

        info_group.setLayout(info_form)

        body_layout.addWidget(info_group)

        # ---------- Progreso de la clase ----------

        progress_group = QGroupBox(tr("Progress"))
        progress_form = QFormLayout()

        FIELD_HEIGHT = 72

        self.conversation_topic = QPlainTextEdit(session.conversation_topic)
        self.conversation_topic.setFixedHeight(FIELD_HEIGHT)
        self.conversation_topic.setTabChangesFocus(True)

        self.grammar_learned = QPlainTextEdit(session.grammar_learned)
        self.grammar_learned.setFixedHeight(FIELD_HEIGHT)
        self.grammar_learned.setTabChangesFocus(True)

        self.homework = QPlainTextEdit(session.homework)
        self.homework.setFixedHeight(FIELD_HEIGHT)
        self.homework.setTabChangesFocus(True)

        self.next_topics = QPlainTextEdit(session.next_topics)
        self.next_topics.setFixedHeight(FIELD_HEIGHT)
        self.next_topics.setTabChangesFocus(True)

        self.homework_done = QCheckBox(
            tr("Completed the homework")
        )

        self.homework_done.setChecked(session.homework_done)

        progress_form.addRow(
            tr("Conversation Topic:"),
            self.conversation_topic,
        )
        progress_form.addRow(
            tr("Grammar Learned:"),
            self.grammar_learned,
        )
        progress_form.addRow(
            tr("Next Task:"),
            self.homework,
        )
        progress_form.addRow(
            tr("To Learn Next:"),
            self.next_topics,
        )
        progress_form.addRow(
            tr("Homework Done"),
            self.homework_done,
        )

        progress_group.setLayout(progress_form)

        body_layout.addWidget(progress_group)

        # ---------- Botones ----------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_edit)
        buttons.rejected.connect(self.reject)

        scroll.setWidget(body)

        layout.addWidget(scroll)
        layout.addWidget(buttons)

        enable_enter_to_next(self)

    def accept_edit(self) -> None:
        """Valida la edición y aplica los cambios a la sesión."""
        start = self.start_time.time()
        end = self.end_time.time()

        if end <= start:
            QMessageBox.warning(
                self,
                tr("Invalid Session"),
                tr("End time must be after start time."),
            )

            return

        self.session.date = self.date.date().toString(
            "yyyy-MM-dd"
        )
        self.session.start_time = start.toString("HH:mm")
        self.session.end_time = end.toString("HH:mm")
        self.session.topic = self.topic.text()
        self.session.status = self.status.currentData()
        self.session.notes = self.notes.text()
        self.session.paid = self.paid.isChecked()
        self.session.conversation_topic = (
            self.conversation_topic.toPlainText()
        )
        self.session.grammar_learned = (
            self.grammar_learned.toPlainText()
        )
        self.session.homework = self.homework.toPlainText()
        self.session.next_topics = self.next_topics.toPlainText()
        self.session.homework_done = (
            self.homework_done.isChecked()
        )

        self.edited_session = self.session

        self.accept()
