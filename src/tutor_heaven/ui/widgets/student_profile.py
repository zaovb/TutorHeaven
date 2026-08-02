from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
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

        # ---------- Enrollment ----------

        enrollment = QWidget()
        enrollment_layout = QVBoxLayout(enrollment)

        history = QTableWidget(1, 7)
        history.setHorizontalHeaderLabels(
            [
                "Name",
                "Type",
                "Total",
                "Classes Left",
                "Next Class",
                "Notes",
                "Status",
            ]
        )

        history.setItem(0, 0, QTableWidgetItem(student.name))
        history.setItem(0, 1, QTableWidgetItem(student.student_type))
        history.setItem(
            0,
            2,
            QTableWidgetItem(f"$ {student.total:.2f}"),
        )
        history.setItem(
            0,
            3,
            QTableWidgetItem(str(student.classes_left)),
        )
        history.setItem(0, 4, QTableWidgetItem("-"))
        history.setItem(0, 5, QTableWidgetItem(student.notes))

        status = (
            "Pay later"
            if student.payment_mode == "Pay later"
            else student.payment_status
        )

        history.setItem(0, 6, QTableWidgetItem(status))

        for row in range(history.rowCount()):
            for column in range(history.columnCount()):
                item = history.item(row, column)

                if item is not None:
                    item.setFlags(
                        item.flags() & ~Qt.ItemFlag.ItemIsEditable
                    )

        enrollment_layout.addWidget(history)

        group = QGroupBox("Enrollment Details")
        form = QFormLayout()

        form.addRow("Email", QLabel(student.email))
        form.addRow("Phone", QLabel(student.phone))
        form.addRow(
            "Hourly Price",
            QLabel(f"$ {student.hourly_price:.2f}"),
        )
        form.addRow(
            "Classes Purchased",
            QLabel(str(student.classes_purchased)),
        )
        form.addRow(
            "Payment Mode",
            QLabel(student.payment_mode),
        )

        group.setLayout(form)

        enrollment_layout.addWidget(group)

        edit_button = QPushButton("Edit Enrollment")
        enrollment_layout.addWidget(edit_button)
        enrollment_layout.addStretch()

        tabs.addTab(enrollment, "Enrollment")

        layout.addWidget(tabs)