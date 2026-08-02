from PySide6.QtWidgets import (
    QListWidget,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.placeholder import Placeholder
from tutor_heaven.ui.widgets.student_dialog import StudentDialog
from tutor_heaven.ui.widgets.student_profile import StudentProfile


class StudentBrowser(QWidget):
    """Main student browser."""

    def __init__(self) -> None:
        super().__init__()

        self.students: list[Student] = []

        layout = QVBoxLayout(self)

        self.new_enrollment = QPushButton("➕ New Enrollment")
        self.new_enrollment.clicked.connect(self.new_enrollment_clicked)

        self.splitter = QSplitter()

        self.student_list = QListWidget()
        self.student_list.currentRowChanged.connect(
            self.student_selected
        )

        self.right_widget = Placeholder(
            "Select a student\n\nto open the profile."
        )

        self.splitter.addWidget(self.student_list)
        self.splitter.addWidget(self.right_widget)

        self.splitter.setSizes([250, 1000])

        layout.addWidget(self.new_enrollment)
        layout.addWidget(self.splitter)

    def new_enrollment_clicked(self) -> None:
        dialog = StudentDialog()

        if not dialog.exec():
            return

        student = dialog.student

        if student is None:
            return

        self.students.append(student)
        self.student_list.addItem(student.name)

    def student_selected(self, row: int) -> None:
        if row < 0:
            return

        self.splitter.replaceWidget(
            1,
            StudentProfile(self.students[row]),
        )