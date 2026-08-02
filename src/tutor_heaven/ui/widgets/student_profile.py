from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.models.student_model import Student


class StudentProfile(QWidget):
    """Student profile."""

    def __init__(self, student: Student) -> None:
        super().__init__()

        self.student = student

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        tabs.addTab(
            self.create_enrollment_tab(),
            "Enrollment",
        )

        layout.addWidget(tabs)

    def create_label(self, text: str) -> QLabel:
        label = QLabel(text)

        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        return label

    def create_enrollment_tab(self) -> QWidget:
        enrollment = QWidget()

        layout = QVBoxLayout(enrollment)

        group = QGroupBox("Enrollment Information")
        form = QFormLayout()

        form.addRow(
            "Name",
            self.create_label(self.student.name),
        )

        form.addRow(
            "Type",
            self.create_label(self.student.student_type),
        )

        form.addRow(
            "Email",
            self.create_label(self.student.email),
        )

        form.addRow(
            "Phone",
            self.create_label(self.student.phone),
        )

        form.addRow(
            "Hourly Price",
            self.create_label(
                f"$ {self.student.hourly_price:.2f}"
            ),
        )

        form.addRow(
            "Classes Purchased",
            self.create_label(
                str(self.student.classes_purchased)
            ),
        )

        form.addRow(
            "Classes Taken",
            self.create_label(
                str(self.student.classes_taken)
            ),
        )

        form.addRow(
            "Classes Left",
            self.create_label(
                str(self.student.classes_left)
            ),
        )

        form.addRow(
            "Total",
            self.create_label(
                f"$ {self.student.total:.2f}"
            ),
        )

        form.addRow(
            "Payment Mode",
            self.create_label(
                self.student.payment_mode
            ),
        )

        form.addRow(
            "Payment Status",
            self.create_label(
                self.student.payment_status
            ),
        )

        form.addRow(
            "Notes",
            self.create_label(
                self.student.notes
            ),
        )

        group.setLayout(form)

        layout.addWidget(group)
        layout.addStretch()

        return enrollment