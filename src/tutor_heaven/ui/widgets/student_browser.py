from PySide6.QtWidgets import (
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.ui.student_profile_window import StudentProfileWindow
from tutor_heaven.ui.widgets.placeholder import Placeholder
from tutor_heaven.ui.widgets.student_enrollments import Students


class StudentBrowser(QWidget):
    """Main student browser."""

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        self.splitter = QSplitter()

        self.enrollments = Students()
        self.enrollments.studentSelected.connect(
            self.open_student_profile
        )

        self.placeholder = Placeholder(
            "Select a student\n\nto open the profile."
        )

        self.splitter.addWidget(self.enrollments)
        self.splitter.addWidget(self.placeholder)

        self.splitter.setSizes([700, 900])

        layout.addWidget(self.splitter)

        self.profile_window = None

    def open_student_profile(self, student) -> None:
        self.profile_window = StudentProfileWindow(student)
        self.profile_window.show()