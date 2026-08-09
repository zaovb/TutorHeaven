from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class SessionProgressDialog(FitDialog):
    """Dialog to record the progress of a class just taught.

    Se abre al marcar una clase como "vista" (consumida). Muestra
    cuántas clases le quedan al estudiante y la tarea pendiente de la
    clase anterior para poder revisarla. Permite escribir el progreso
    del día (gramática aprendida, tarea para la próxima, temas por
    ver, tema de conversación) y añadir intereses del estudiante.

    Al aceptar expone en self.session_data un dict con los campos de
    progreso y en self.new_interests las nuevas etiquetas de interés.
    """

    def __init__(
        self,
        student: Student,
    ) -> None:
        super().__init__()

        self.student = student

        self.session_data = None
        self.new_interests: list[str] = []

        self.setWindowTitle(tr("Class Progress"))
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # ---------- Info de la clase ----------

        info_group = QGroupBox(tr("Class Information"))
        info_layout = QFormLayout()

        self.classes_left = QLabel()
        self.last_homework = QLabel()

        info_layout.addRow(tr("Classes Available"), self.classes_left)
        info_layout.addRow(tr("Last Homework"), self.last_homework)

        # Chulito para marcar si el estudiante hizo la tarea previa.
        self.homework_done = QCheckBox(
            tr("Completed the homework")
        )

        info_layout.addRow(tr("Homework Done"), self.homework_done)

        info_group.setLayout(info_layout)

        layout.addWidget(info_group)

        # ---------- Progreso del día ----------

        progress_group = QGroupBox(tr("Today's Progress"))
        progress_layout = QFormLayout()

        self.conversation_topic = QLineEdit()

        self.grammar_learned = QPlainTextEdit()
        self.grammar_learned.setMaximumHeight(80)

        self.homework = QPlainTextEdit()
        self.homework.setMaximumHeight(80)

        self.next_topics = QPlainTextEdit()
        self.next_topics.setMaximumHeight(80)

        progress_layout.addRow(tr("Conversation Topic"), self.conversation_topic)
        progress_layout.addRow(tr("Grammar Learned"), self.grammar_learned)
        progress_layout.addRow(tr("Homework"), self.homework)
        progress_layout.addRow(tr("To Learn Next"), self.next_topics)

        progress_group.setLayout(progress_layout)

        layout.addWidget(progress_group)

        # ---------- Intereses del estudiante ----------

        interests_group = QGroupBox(tr("Student Interests"))
        interests_layout = QVBoxLayout()

        self.interests_list = QListWidget()

        self.refresh_interests()

        self.new_interest = QLineEdit()
        self.new_interest.setPlaceholderText(
            tr("Add an interest (hobby, topic...)")
        )

        # Al pulsar Enter se añade el interés sin cerrar el diálogo.
        self.new_interest._enter_action = self.add_interest

        add_button = QPushButton(tr("➕ Add Interest"))
        add_button.clicked.connect(
            self.add_interest
        )

        remove_button = QPushButton(tr("Remove Selected"))
        remove_button.clicked.connect(
            self.remove_interest
        )

        add_row = QHBoxLayout()

        add_row.addWidget(self.new_interest)
        add_row.addWidget(add_button)

        interests_layout.addWidget(self.interests_list)
        interests_layout.addLayout(add_row)
        interests_layout.addWidget(remove_button)

        interests_group.setLayout(interests_layout)

        layout.addWidget(interests_group)

        # ---------- Botones ----------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # Enter = siguiente campo (sin cerrar el diálogo).
        enable_enter_to_next(self)

        self.update_info()

    def update_info(self) -> None:
        """Rellena las etiquetas de clases disponibles y tarea previa."""
        self.classes_left.setText(
            str(self.student.classes_left)
        )

        # Muestra la tarea de la última sesión registrada (si hay)
        # para poder revisarla en esta clase.
        last_homework = self.last_session_homework()

        self.last_homework.setText(
            last_homework
            if last_homework
            else "No previous homework"
        )

        # Permite seleccionar el texto de la tarea para leerlo/copiarlo.
        self.last_homework.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        self.last_homework.setWordWrap(True)

    def last_session_homework(self) -> str:
        """Devuelve la tarea de la sesión más reciente, o "" si no hay."""
        if not self.student.sessions:
            return ""

        latest = max(
            self.student.sessions,
            key=lambda session: session.start_datetime,
        )

        return latest.homework

    def refresh_interests(self) -> None:
        """Muestra los intereses actuales del estudiante."""
        self.interests_list.clear()

        # Intereses ya guardados en el estudiante más los nuevos que
        # se vayan añadiendo en este diálogo.
        all_interests = [
            *self.student.interests,
            *self.new_interests,
        ]

        # Elimina duplicados conservando el orden.
        seen = set()
        unique = []

        for interest in all_interests:
            if interest not in seen:
                seen.add(interest)
                unique.append(interest)

        self.interests_list.addItems(unique)

    def add_interest(self) -> None:
        """Añade el interés escrito al cuadro de intereses."""
        text = self.new_interest.text().strip()

        if not text:
            return

        if (
            text in self.student.interests
            or text in self.new_interests
        ):
            QMessageBox.information(
                self,
                "Interest",
                "That interest is already added.",
            )

            return

        self.new_interests.append(text)

        self.new_interest.clear()

        self.refresh_interests()

    def remove_interest(self) -> None:
        """Elimina el interés seleccionado (si es nuevo en el diálogo)."""
        row = self.interests_list.currentRow()

        if row < 0:
            return

        text = self.interests_list.currentItem().text()

        # Solo se pueden quitar los intereses añadidos en este diálogo;
        # los ya guardados del estudiante se mantienen.
        if text in self.new_interests:
            self.new_interests.remove(text)

            self.refresh_interests()

    def accept_dialog(self) -> None:
        self.session_data = {
            "date": QDate.currentDate().toString(
                "yyyy-MM-dd"
            ),
            "start_time": QTime.currentTime().toString(
                "HH:mm"
            ),
            "end_time": QTime.currentTime().addSecs(
                3600
            ).toString(
                "HH:mm"
            ),
            "topic": self.conversation_topic.text(),
            "status": "Completed",
            "notes": "",
            "paid": self.student.session_paid_default(),
            "conversation_topic": self.conversation_topic.text(),
            "grammar_learned": self.grammar_learned.toPlainText(),
            "homework": self.homework.toPlainText(),
            "next_topics": self.next_topics.toPlainText(),
            "homework_done": self.homework_done.isChecked(),
        }

        self.accept()
