from PySide6.QtWidgets import (
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

from tutor_heaven.data.student_storage import save_students
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class ResumeDialog(FitDialog):
    """Dialog to view and edit a student's resume (hoja de vida).

    Reúne la información general del estudiante, su biografía (bio) y
    los intereses acumulados. Los intereses se pueden leer, añadir y
    eliminar aquí. Los cambios se guardan en disco al aceptar.
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
            f"{tr('Curriculum (Resume)')} — {student.name}"
        )
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # ---------- Información general ----------

        info_group = QGroupBox(
            tr("General Information")
        )

        info_layout = QFormLayout()

        fields = [
            (
                tr("Name"),
                student.name,
            ),
            (
                tr("Level"),
                student.level or "—",
            ),
            (
                tr("Email"),
                student.email,
            ),
            (
                tr("Phone"),
                student.phone,
            ),
            (
                tr("Enrolled On"),
                student.enrolled_at,
            ),
        ]

        for title, value in fields:
            info_layout.addRow(
                title,
                QLabel(value),
            )

        info_group.setLayout(info_layout)

        layout.addWidget(info_group)

        # ---------- Biografía ----------

        bio_group = QGroupBox(
            tr("About the Student")
        )

        bio_layout = QVBoxLayout()

        self.bio = QPlainTextEdit()
        self.bio.setPlaceholderText(
            tr(
                "Write a short bio: background, goals, level, anything useful..."
            )
        )
        self.bio.setPlainText(student.bio)

        bio_layout.addWidget(self.bio)

        bio_group.setLayout(bio_layout)

        layout.addWidget(bio_group)

        # ---------- Intereses ----------

        interests_group = QGroupBox(
            tr("Interests")
        )

        interests_layout = QVBoxLayout()

        self.interests_list = QListWidget()

        self.refresh_interests()

        self.new_interest = QLineEdit()
        self.new_interest.setPlaceholderText(
            tr("Add an interest (hobby, topic...)")
        )

        # Al pulsar Enter se añade el interés sin cerrar el diálogo
        # (en lugar de activar el botón OK).
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

    def refresh_interests(self) -> None:
        """Muestra los intereses actuales del estudiante."""
        self.interests_list.clear()

        self.interests_list.addItems(
            self.student.interests
        )

    def add_interest(self) -> None:
        """Añade el interés escrito a la lista del estudiante."""
        text = self.new_interest.text().strip()

        if not text:
            return

        if text in self.student.interests:
            QMessageBox.information(
                self,
                tr("Interest"),
                tr("That interest is already added."),
            )

            return

        self.student.interests.append(text)

        self.new_interest.clear()

        self.refresh_interests()

    def remove_interest(self) -> None:
        """Elimina el interés seleccionado del estudiante."""
        row = self.interests_list.currentRow()

        if row < 0:
            return

        del self.student.interests[row]

        self.refresh_interests()

    def accept_dialog(self) -> None:
        """Guarda la bio editada y los intereses en disco."""
        self.student.bio = self.bio.toPlainText()

        save_students(
            self.students
        )

        self.accept()
