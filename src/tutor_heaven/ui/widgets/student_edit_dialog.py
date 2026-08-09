from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from tutor_heaven.data.student_storage import save_students
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next

LEVELS = [
    "",
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
]


class StudentEditDialog(FitDialog):
    """Dialog to edit a student's profile information.

    Permite modificar la información del estudiante (nombre, email,
    teléfono, tipo, nivel, temas gramaticales, notas). Los cambios se
    aplican al estudiante solo si el usuario los confirma explícitamente
    antes de guardar.
    """

    def __init__(
        self,
        student: Student,
        students: list[Student],
    ) -> None:
        super().__init__()

        self.student = student
        self.students = students

        self.setWindowTitle(
            f"{tr('Edit Student')} — {student.name}"
        )
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)

        # ---------- Información básica ----------

        basic_group = QGroupBox(tr("Basic Information"))
        basic_layout = QFormLayout()

        self.name = QLineEdit(student.name)

        self.student_type = QComboBox()
        self.student_type.addItems(
            [
                "Individual",
                "Group",
                "Custom",
            ]
        )
        self.student_type.setCurrentText(student.student_type)

        self.level = QComboBox()
        self.level.addItems(LEVELS)
        self.level.setCurrentText(student.level)

        self.email = QLineEdit(student.email)
        self.phone = QLineEdit(student.phone)

        basic_layout.addRow(tr("Name"), self.name)
        basic_layout.addRow(tr("Type"), self.student_type)
        basic_layout.addRow(tr("Level"), self.level)
        basic_layout.addRow(tr("Email"), self.email)
        basic_layout.addRow(tr("Phone"), self.phone)

        basic_group.setLayout(basic_layout)

        layout.addWidget(basic_group)

        # ---------- Temas gramaticales ----------

        topics_group = QGroupBox(tr("Grammar Topics"))
        topics_layout = QVBoxLayout()

        self.topics_list = QListWidget()

        self.refresh_topics()

        self.new_topic = QLineEdit()
        self.new_topic.setPlaceholderText(
            tr("Add a grammar topic (e.g. Present Perfect)")
        )

        # Enter añade el tema sin cerrar el diálogo.
        self.new_topic._enter_action = self.add_topic

        add_button = QPushButton(tr("➕ Add Topic"))
        add_button.clicked.connect(
            self.add_topic
        )

        remove_button = QPushButton(tr("Remove Selected"))
        remove_button.clicked.connect(
            self.remove_topic
        )

        add_row = QHBoxLayout()

        add_row.addWidget(self.new_topic)
        add_row.addWidget(add_button)

        topics_layout.addWidget(self.topics_list)
        topics_layout.addLayout(add_row)
        topics_layout.addWidget(remove_button)

        topics_group.setLayout(topics_layout)

        layout.addWidget(topics_group)

        # ---------- Notas ----------

        notes_group = QGroupBox(tr("Notes"))
        notes_layout = QVBoxLayout()

        self.notes = QPlainTextEdit()
        self.notes.setPlainText(student.notes)

        notes_layout.addWidget(self.notes)

        notes_group.setLayout(notes_layout)

        layout.addWidget(notes_group)

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

    def refresh_topics(self) -> None:
        """Muestra los temas gramaticales actuales del estudiante."""
        self.topics_list.clear()

        self.topics_list.addItems(
            self.student.topics
        )

    def add_topic(self) -> None:
        """Añade el tema gramatical escrito a la lista."""
        text = self.new_topic.text().strip()

        if not text:
            return

        if text in self.student.topics:
            QMessageBox.information(
                self,
                tr("Grammar Topic"),
                tr("That topic is already added."),
            )

            return

        self.student.topics.append(text)

        self.new_topic.clear()

        self.refresh_topics()

    def remove_topic(self) -> None:
        """Elimina el tema gramatical seleccionado."""
        row = self.topics_list.currentRow()

        if row < 0:
            return

        del self.student.topics[row]

        self.refresh_topics()

    def accept_dialog(self) -> None:
        """Pide confirmación y aplica los cambios al estudiante."""
        new_values = {
            "name": self.name.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "level": self.level.currentText(),
            "notes": self.notes.toPlainText(),
        }

        confirm = QMessageBox.question(
            self,
            tr("Confirm Changes"),
            tr(
                "Do you want to apply these changes to {0}?"
            ).format(
                new_values["name"] or self.student.name
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.student.name = new_values["name"]
        self.student.student_type = self.student_type.currentText()
        self.student.level = new_values["level"]
        self.student.email = new_values["email"]
        self.student.phone = new_values["phone"]
        self.student.notes = new_values["notes"]

        save_students(
            self.students
        )

        self.accept()
