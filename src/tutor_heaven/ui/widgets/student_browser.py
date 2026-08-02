from PySide6.QtWidgets import (
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.ui.widgets.placeholder import Placeholder
from tutor_heaven.ui.widgets.student_enrollments import Students
from tutor_heaven.ui.widgets.student_profile import StudentProfile


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

        self.profile = self.placeholder

        self.splitter.addWidget(
            self.enrollments
        )

        self.splitter.addWidget(
            self.profile
        )

        self.splitter.setSizes(
            [
                400,
                900,
            ]
        )

        layout.addWidget(
            self.splitter
        )

    def open_student_profile(
        self,
        student,
    ) -> None:
        new_profile = StudentProfile(
            student,
            self.enrollments.students,
        )

        self.splitter.replaceWidget(
            1,
            new_profile,
        )

        self.profile.deleteLater()

        self.profile = new_profile