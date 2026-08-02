from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.student_storage import (
    load_students,
    save_students,
)
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.student_dialog import StudentDialog


class Students(QWidget):
    """Students module."""

    studentSelected = Signal(object)

    def __init__(self) -> None:
        super().__init__()

        self.students: list[Student] = load_students()

        layout = QVBoxLayout(self)

        new_student_button = QPushButton(
            "➕ New Enrollment"
        )

        new_student_button.clicked.connect(
            self.new_student
        )

        self.list = QListWidget()

        self.list.itemClicked.connect(
            self.show_enrollment
        )

        self.list.itemDoubleClicked.connect(
            self.open_student
        )

        self.details = QWidget()

        details_layout = QFormLayout(
            self.details
        )

        self.total = QLabel("-")
        self.classes_left = QLabel("-")
        self.next_class = QLabel("-")
        self.notes = QLabel("-")
        self.status = QLabel("-")

        details_layout.addRow(
            "Total",
            self.total,
        )

        details_layout.addRow(
            "Classes Left",
            self.classes_left,
        )

        details_layout.addRow(
            "Next Class",
            self.next_class,
        )

        details_layout.addRow(
            "Notes",
            self.notes,
        )

        details_layout.addRow(
            "Status",
            self.status,
        )

        layout.addWidget(
            new_student_button
        )

        layout.addWidget(
            self.list
        )

        layout.addWidget(
            self.details
        )

        self.refresh_students()

    def refresh_students(self) -> None:
        self.list.clear()

        for student in self.students:
            self.list.addItem(
                student.name
            )

    def new_student(self) -> None:
        dialog = StudentDialog()

        if not dialog.exec():
            return

        student = dialog.student

        if student is None:
            return

        self.students.append(
            student
        )

        save_students(
            self.students
        )

        self.refresh_students()

    def show_enrollment(self) -> None:
        row = self.list.currentRow()

        if row < 0:
            return

        student = self.students[row]

        self.total.setText(
            f"$ {student.total:.2f}"
        )

        self.classes_left.setText(
            str(student.classes_left)
        )

        self.next_class.setText(
            "-"
        )

        self.notes.setText(
            student.notes
        )

        status = (
            "Pay later"
            if student.payment_mode == "Pay later"
            else student.payment_status
        )

        self.status.setText(
            status
        )

    def open_student(self) -> None:
        row = self.list.currentRow()

        if row < 0:
            return

        self.studentSelected.emit(
            self.students[row]
        )